#!/usr/bin/env python3
"""
Test script for image source and output nodes.
"""

import sys
import os
import pytest

Image = pytest.importorskip("PIL.Image", reason="Pillow not installed")
import io

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

# Import directly from module files to avoid circular imports
# Import packet directly from file
import importlib.util
spec = importlib.util.spec_from_file_location("packet", "src/core/packet.py")
packet_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packet_module)

# Import source nodes directly from file
spec2 = importlib.util.spec_from_file_location("sources", "src/nodes/sources.py")
sources_module = importlib.util.module_from_spec(spec2)
sys.modules['src.nodes.sources'] = sources_module
spec2.loader.exec_module(sources_module)

# Import sink nodes directly from file  
spec3 = importlib.util.spec_from_file_location("sinks", "src/nodes/sinks.py")
sinks_module = importlib.util.module_from_spec(spec3)
sys.modules['src.nodes.sinks'] = sinks_module
spec3.loader.exec_module(sinks_module)

# Get classes directly from modules
DataPacket = packet_module.DataPacket
ImageSourceNode = sources_module.ImageSourceNode
ImageOutputNode = sinks_module.ImageOutputNode


def create_test_image(path: str, size: tuple = (100, 100)):
    """Create a simple test image."""
    img = Image.new('RGB', size, color='red')
    img.save(path)
    print(f"✓ Created test image: {path} ({size[0]}x{size[1]})")


def test_image_source_node():
    """Test ImageSourceNode with a real image file."""
    print("\n=== Testing ImageSourceNode ===")
    
    # Create test image
    test_image_path = "test_image.png"
    create_test_image(test_image_path, (200, 150))
    
    # Create node
    node = ImageSourceNode("test_img_src")
    
    # Set file path parameter
    node.set_param("file_path", test_image_path)
    
    # Create a dummy packet
    dummy_packet = DataPacket(id="test_pkt", payload=b"")
    
    # Process the image
    print(f"Processing image from: {test_image_path}")
    result = node.process(dummy_packet, "in")
    
    # Check results
    if result.payload:
        print(f"✓ Image loaded successfully!")
        print(f"  - Payload size: {len(result.payload)} bytes")
        print(f"  - Size bits: {result.size_bits}")
        print(f"  - Source format: {result.source_format}")
        
        # Verify we can load it back
        try:
            img = Image.open(io.BytesIO(result.payload))
            print(f"✓ Image verified: {img.width}x{img.height} {img.mode}")
            return True
        except Exception as e:
            print(f"✗ Failed to verify image: {e}")
            return False
    else:
        print(f"✗ No payload returned")
        if result.history:
            print(f"  History: {result.history[-1].details}")
        return False


def test_image_output_node():
    """Test ImageOutputNode with image data."""
    print("\n=== Testing ImageOutputNode ===")
    
    # Create a simple image in memory
    img = Image.new('RGB', (100, 100), color='blue')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()
    
    # Create node
    node = ImageOutputNode("test_img_out")
    
    # Create packet with image data
    packet = DataPacket(id="test_pkt", payload=image_bytes, source_format="image")
    
    # Process
    print(f"Processing image output ({len(image_bytes)} bytes)")
    result = node.process(packet, "in")
    
    # Check results
    if node.last_image_size:
        print(f"✓ Image output processed!")
        print(f"  - Size: {node.last_image_size}")
        print(f"  - Format: {node.last_image_format}")
        
        if result.history:
            print(f"  - History: {result.history[-1].details}")
        return True
    else:
        print(f"✗ Failed to process image output")
        return False


def test_error_handling():
    """Test error handling with invalid file."""
    print("\n=== Testing Error Handling ===")
    
    node = ImageSourceNode("test_error")
    node.set_param("file_path", "/nonexistent/path/to/image.png")
    
    dummy_packet = DataPacket(id="test_pkt", payload=b"")
    result = node.process(dummy_packet, "in")
    
    if not result.payload and result.history:
        print(f"✓ Error handled correctly: {result.history[-1].details}")
        return True
    else:
        print(f"✗ Error not handled properly")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Image Node Tests")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(("ImageSourceNode", test_image_source_node()))
    except Exception as e:
        print(f"✗ ImageSourceNode test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("ImageSourceNode", False))
    
    try:
        results.append(("ImageOutputNode", test_image_output_node()))
    except Exception as e:
        print(f"✗ ImageOutputNode test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("ImageOutputNode", False))
    
    try:
        results.append(("ErrorHandling", test_error_handling()))
    except Exception as e:
        print(f"✗ Error handling test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("ErrorHandling", False))
    
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