#!/usr/bin/env python3
"""
Test advanced image processing flow with error simulation.
"""

import sys
import os
import pytest

Image = pytest.importorskip("PIL.Image", reason="Pillow not installed")
import io

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

# Import directly from module files to avoid circular imports
import importlib.util

# Import packet directly
spec = importlib.util.spec_from_file_location("packet", "src/core/packet.py")
packet_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packet_module)

# Import image nodes
spec2 = importlib.util.spec_from_file_location("image_nodes", "src/nodes/image_nodes.py")
image_nodes_module = importlib.util.module_from_spec(spec2)
sys.modules['src.nodes.image_nodes'] = image_nodes_module
spec2.loader.exec_module(image_nodes_module)

# Import source nodes
spec3 = importlib.util.spec_from_file_location("sources", "src/nodes/sources.py")
sources_module = importlib.util.module_from_spec(spec3)
sys.modules['src.nodes.sources'] = sources_module
spec3.loader.exec_module(sources_module)

# Import sink nodes
spec4 = importlib.util.spec_from_file_location("sinks", "src/nodes/sinks.py")
sinks_module = importlib.util.module_from_spec(spec4)
sys.modules['src.nodes.sinks'] = sinks_module
spec4.loader.exec_module(sinks_module)

# Get classes
DataPacket = packet_module.DataPacket
ImageSourceNode = sources_module.ImageSourceNode
ImageOutputNode = sinks_module.ImageOutputNode
ImageBlockLossNode = image_nodes_module.ImageBlockLossNode
ImageTransformNode = image_nodes_module.ImageTransformNode
ImageComparatorNode = image_nodes_module.ImageComparatorNode


def create_test_image(path: str, size: tuple = (100, 100), color: str = 'red'):
    """Create a simple test image."""
    img = Image.new('RGB', size, color=color)
    img.save(path)
    print(f"✓ Created test image: {path} ({size[0]}x{size[1]})")


def test_block_loss():
    """Test ImageBlockLossNode."""
    print("\n=== Testing ImageBlockLossNode ===")
    
    # Create test image
    test_image_path = "test_block_loss.png"
    create_test_image(test_image_path, (64, 64), 'blue')
    
    # Create source node
    source = ImageSourceNode("src")
    source.set_param("file_path", test_image_path)
    
    # Create block loss node
    block_loss = ImageBlockLossNode("block_loss")
    block_loss.set_param("block_size", 16)
    block_loss.set_param("loss_probability", 0.3)
    block_loss.set_param("replace_with", "black")
    
    # Process
    packet1 = DataPacket(id="pkt1", payload=b"")
    packet2 = source.process(packet1, "in")
    
    if not packet2.payload:
        print("✗ Source failed to load image")
        return False
    
    print(f"✓ Source loaded image: {len(packet2.payload)} bytes")
    
    packet3 = block_loss.process(packet2, "in")
    
    if packet3.payload and packet3.history:
        last_step = packet3.history[-1]
        print(f"✓ Block loss applied: {last_step.details}")
        
        # Verify image is still valid
        try:
            img = Image.open(io.BytesIO(packet3.payload))
            print(f"✓ Result is valid image: {img.width}x{img.height}")
            return True
        except Exception as e:
            print(f"✗ Result is not valid image: {e}")
            return False
    else:
        print("✗ Block loss failed")
        return False


def test_transform():
    """Test ImageTransformNode."""
    print("\n=== Testing ImageTransformNode ===")
    
    # Create test image
    test_image_path = "test_transform.png"
    create_test_image(test_image_path, (100, 100), 'green')
    
    # Create source
    source = ImageSourceNode("src")
    source.set_param("file_path", test_image_path)
    
    # Create transform node
    transform = ImageTransformNode("transform")
    transform.set_param("rotation", 90)
    transform.set_param("flip_h", True)
    transform.set_param("noise_amount", 20)
    
    # Process
    packet1 = DataPacket(id="pkt1", payload=b"")
    packet2 = source.process(packet1, "in")
    
    if not packet2.payload:
        print("✗ Source failed")
        return False
    
    packet3 = transform.process(packet2, "in")
    
    if packet3.payload and packet3.history:
        last_step = packet3.history[-1]
        print(f"✓ Transform applied: {last_step.details}")
        
        # Verify
        try:
            img = Image.open(io.BytesIO(packet3.payload))
            print(f"✓ Result is valid image: {img.width}x{img.height}")
            return True
        except Exception as e:
            print(f"✗ Result is not valid image: {e}")
            return False
    else:
        print("✗ Transform failed")
        return False


def test_comparator():
    """Test ImageComparatorNode."""
    print("\n=== Testing ImageComparatorNode ===")
    
    # Create two different images
    img1_path = "test_comp_a.png"
    img2_path = "test_comp_b.png"
    create_test_image(img1_path, (50, 50), 'red')
    create_test_image(img2_path, (50, 50), 'blue')
    
    # Create source nodes
    source_a = ImageSourceNode("src_a")
    source_a.set_param("file_path", img1_path)
    
    source_b = ImageSourceNode("src_b")
    source_b.set_param("file_path", img2_path)
    
    # Create comparator
    comparator = ImageComparatorNode("compare")
    comparator.set_param("show_diff", True)
    
    # Process
    packet1 = DataPacket(id="pkt1", payload=b"")
    packet2 = source_a.process(packet1, "in")
    packet3 = DataPacket(id="pkt2", payload=b"")
    packet4 = source_b.process(packet3, "in")
    
    if not packet2.payload or not packet4.payload:
        print("✗ Sources failed")
        return False
    
    # Send to comparator
    packet5 = comparator.process(packet2, "in_a")
    packet6 = comparator.process(packet5, "in_b")
    
    if hasattr(comparator, 'last_mse') and comparator.last_mse > 0:
        print(f"✓ Comparison complete:")
        print(f"  MSE: {comparator.last_mse:.2f}")
        print(f"  PSNR: {comparator.last_psnr:.1f} dB")
        print(f"  Diff: {comparator.last_diff_percent:.1f}%")
        
        if packet6.payload:
            print(f"✓ Diff image generated: {len(packet6.payload)} bytes")
            return True
        else:
            print("✗ No diff image generated")
            return False
    else:
        print("✗ Comparison failed")
        return False


def test_full_flow():
    """Test complete flow: Source → BlockLoss → Transform → Output."""
    print("\n=== Testing Full Flow ===")
    
    # Create test image
    test_image_path = "test_full_flow.png"
    create_test_image(test_image_path, (128, 128), 'yellow')
    
    # Create nodes
    source = ImageSourceNode("source")
    source.set_param("file_path", test_image_path)
    
    block_loss = ImageBlockLossNode("block_loss")
    block_loss.set_param("block_size", 16)
    block_loss.set_param("loss_probability", 0.2)
    block_loss.set_param("replace_with", "noise")
    
    transform = ImageTransformNode("transform")
    transform.set_param("rotation", 0)
    transform.set_param("noise_amount", 10)
    
    output = ImageOutputNode("output")
    
    # Process flow
    print("1. Loading image...")
    p1 = DataPacket(id="p1", payload=b"")
    p2 = source.process(p1, "in")
    
    if not p2.payload:
        print("✗ Failed at source")
        return False
    print(f"   ✓ Loaded: {len(p2.payload)} bytes")
    
    print("2. Applying block loss...")
    p3 = block_loss.process(p2, "in")
    
    if not p3.payload:
        print("✗ Failed at block loss")
        return False
    print(f"   ✓ Block loss applied")
    
    print("3. Applying transform...")
    p4 = transform.process(p3, "in")
    
    if not p4.payload:
        print("✗ Failed at transform")
        return False
    print(f"   ✓ Transform applied")
    
    print("4. Output processing...")
    p5 = output.process(p4, "in")
    
    if output.last_image_size:
        print(f"   ✓ Output: {output.last_image_size}, {output.last_image_format}")
        print(f"   ✓ Preview stored: {output.last_image_bytes is not None}")
        return True
    else:
        print("✗ Failed at output")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Advanced Image Flow Tests")
    print("=" * 60)
    
    results = []
    
    tests = [
        ("BlockLoss", test_block_loss),
        ("Transform", test_transform),
        ("Comparator", test_comparator),
        ("FullFlow", test_full_flow),
    ]
    
    for name, test_func in tests:
        try:
            results.append((name, test_func()))
        except Exception as e:
            print(f"\n✗ {name} test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return all(p for _, p in results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)