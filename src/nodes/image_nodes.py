"""
Image-specific processing nodes - block errors, transformations, and analysis.
"""

import random
import math
from src.core.node_base import NodeBase, ParamType
from src.core.packet import DataPacket
from src.core.port import DataType


class ImageBlockLossNode(NodeBase):
    """Simulate block-level data loss (like JPEG compression artifacts)."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "channel", "📦 BlockLoss", category="channels")
        self.add_input("in", DataType.IMAGE)
        self.add_output("out", DataType.IMAGE)
        self.set_param("block_size", 16)
        self.set_param("loss_probability", 0.1)
        self.set_param("replace_with", "black")
    
    def get_param_schema(self) -> dict:
        schema = super().get_param_schema()
        schema.update({
            "block_size": {
                "type": ParamType.INT, "label": "Block Size", "default": 16,
                "min": 8, "max": 64, "step": 8,
                "description": "Size of blocks to lose (pixels)",
                "category": "basic"
            },
            "loss_probability": {
                "type": ParamType.FLOAT, "label": "Loss Prob", "default": 0.1,
                "min": 0.0, "max": 1.0, "step": 0.05,
                "description": "Probability of losing each block",
                "category": "basic"
            },
            "replace_with": {
                "type": ParamType.CHOICE, "label": "Replace With", "default": "black",
                "choices": ["black", "white", "gray", "noise"],
                "description": "What to replace lost blocks with",
                "category": "basic"
            }
        })
        return schema
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        if not packet.payload:
            return packet
        
        try:
            from PIL import Image
            import io
            import numpy as np
            
            # Load image
            img = Image.open(io.BytesIO(packet.payload))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Convert to numpy array
            data = np.array(img)
            h, w = data.shape[:2]
            
            # Get parameters
            block_size = self.get_param("block_size", 16)
            loss_prob = self.get_param("loss_probability", 0.1)
            replace_mode = self.get_param("replace_with", "black")
            
            # Process blocks
            blocks_lost = 0
            for y in range(0, h - block_size + 1, block_size):
                for x in range(0, w - block_size + 1, block_size):
                    if random.random() < loss_prob:
                        # Lose this block
                        if replace_mode == "black":
                            data[y:y+block_size, x:x+block_size] = [0, 0, 0]
                        elif replace_mode == "white":
                            data[y:y+block_size, x:x+block_size] = [255, 255, 255]
                        elif replace_mode == "gray":
                            data[y:y+block_size, x:x+block_size] = [128, 128, 128]
                        elif replace_mode == "noise":
                            noise = np.random.randint(0, 256, (block_size, block_size, 3))
                            data[y:y+block_size, x:x+block_size] = noise
                        blocks_lost += 1
            
            # Convert back to image
            result_img = Image.fromarray(data, 'RGB')
            buffer = io.BytesIO()
            result_img.save(buffer, format='PNG')
            result_bytes = buffer.getvalue()
            
            # Create new packet
            new_pkt = DataPacket(id=packet.id, payload=result_bytes,
                                source_format="image", size_bits=len(result_bytes)*8)
            new_pkt.add_step(self.name, "BlockLoss", len(packet.payload), len(result_bytes),
                           f"blocks_lost={blocks_lost}, size={block_size}px")
            return new_pkt
            
        except Exception as e:
            packet.add_step(self.name, "BlockLoss", len(packet.payload), len(packet.payload),
                          f"ERROR: {str(e)}")
            return packet


class ImageTransformNode(NodeBase):
    """Apply transformations and corruptions to images."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "processor", "🔄 Transform", category="signal")
        self.add_input("in", DataType.IMAGE)
        self.add_output("out", DataType.IMAGE)
        self.set_param("rotation", 0)
        self.set_param("flip_h", False)
        self.set_param("flip_v", False)
        self.set_param("crop_percent", 0)
        self.set_param("noise_amount", 0)
    
    def get_param_schema(self) -> dict:
        schema = super().get_param_schema()
        schema.update({
            "rotation": {
                "type": ParamType.INT, "label": "Rotation", "default": 0,
                "min": 0, "max": 270, "step": 90,
                "description": "Rotation in degrees (0, 90, 180, 270)",
                "category": "basic"
            },
            "flip_h": {
                "type": ParamType.BOOL, "label": "Flip Horizontal", "default": False,
                "description": "Mirror image horizontally",
                "category": "basic"
            },
            "flip_v": {
                "type": ParamType.BOOL, "label": "Flip Vertical", "default": False,
                "description": "Mirror image vertically",
                "category": "basic"
            },
            "crop_percent": {
                "type": ParamType.INT, "label": "Crop %", "default": 0,
                "min": 0, "max": 50,
                "description": "Crop percentage from each side",
                "category": "basic"
            },
            "noise_amount": {
                "type": ParamType.INT, "label": "Noise", "default": 0,
                "min": 0, "max": 100,
                "description": "Add random noise (0-100)",
                "category": "basic"
            }
        })
        return schema
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        if not packet.payload:
            return packet
        
        try:
            from PIL import Image, ImageOps
            import io
            import numpy as np
            
            # Load image
            img = Image.open(io.BytesIO(packet.payload))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Get parameters
            rotation = self.get_param("rotation", 0)
            flip_h = self.get_param("flip_h", False)
            flip_v = self.get_param("flip_v", False)
            crop_pct = self.get_param("crop_percent", 0)
            noise_amt = self.get_param("noise_amount", 0)
            
            # Apply rotation
            if rotation > 0:
                img = img.rotate(rotation, expand=True)
            
            # Apply flips
            if flip_h:
                img = ImageOps.mirror(img)
            if flip_v:
                img = ImageOps.flip(img)
            
            # Apply crop
            if crop_pct > 0:
                w, h = img.size
                crop_w = int(w * crop_pct / 100)
                crop_h = int(h * crop_pct / 100)
                img = img.crop((crop_w, crop_h, w - crop_w, h - crop_h))
            
            # Apply noise
            if noise_amt > 0:
                data = np.array(img)
                noise = np.random.randint(-noise_amt, noise_amt + 1, data.shape)
                noisy_data = np.clip(data.astype(np.int16) + noise, 0, 255).astype(np.uint8)
                img = Image.fromarray(noisy_data, 'RGB')
            
            # Save result
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            result_bytes = buffer.getvalue()
            
            # Create new packet
            new_pkt = DataPacket(id=packet.id, payload=result_bytes,
                                source_format="image", size_bits=len(result_bytes)*8)
            
            transforms = []
            if rotation > 0:
                transforms.append(f"rot={rotation}°")
            if flip_h:
                transforms.append("flipH")
            if flip_v:
                transforms.append("flipV")
            if crop_pct > 0:
                transforms.append(f"crop={crop_pct}%")
            if noise_amt > 0:
                transforms.append(f"noise={noise_amt}")
            
            new_pkt.add_step(self.name, "Transform", len(packet.payload), len(result_bytes),
                           ", ".join(transforms) if transforms else "no change")
            return new_pkt
            
        except Exception as e:
            packet.add_step(self.name, "Transform", len(packet.payload), len(packet.payload),
                          f"ERROR: {str(e)}")
            return packet


class ImageComparatorNode(NodeBase):
    """Compare two images and calculate differences."""
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "analyzer", "🔍 Compare", category="analyzers")
        self.add_input("in_a", DataType.IMAGE)
        self.add_input("in_b", DataType.IMAGE)
        self.add_output("out", DataType.IMAGE)
        self.last_mse = 0.0
        self.last_psnr = 0.0
        self.last_diff_percent = 0.0
    
    def get_param_schema(self) -> dict:
        schema = super().get_param_schema()
        schema.update({
            "show_diff": {
                "type": ParamType.BOOL, "label": "Show Diff", "default": True,
                "description": "Output difference image",
                "category": "basic"
            }
        })
        return schema
    
    def process(self, packet: DataPacket, input_port: str) -> DataPacket:
        # Store the packet for comparison
        if input_port == "in_a":
            self._packet_a = packet
        elif input_port == "in_b":
            self._packet_b = packet
        
        # Need both packets to compare
        if not hasattr(self, '_packet_a') or not hasattr(self, '_packet_b'):
            return packet
        
        if not self._packet_a.payload or not self._packet_b.payload:
            return packet
        
        try:
            from PIL import Image
            import io
            import numpy as np
            
            # Load both images
            img_a = Image.open(io.BytesIO(self._packet_a.payload))
            img_b = Image.open(io.BytesIO(self._packet_b.payload))
            
            if img_a.mode != 'RGB':
                img_a = img_a.convert('RGB')
            if img_b.mode != 'RGB':
                img_b = img_b.convert('RGB')
            
            # Resize to match if needed
            if img_a.size != img_b.size:
                img_b = img_b.resize(img_a.size, Image.Resampling.LANCZOS)
            
            # Convert to numpy
            arr_a = np.array(img_a, dtype=np.float64)
            arr_b = np.array(img_b, dtype=np.float64)
            
            # Calculate MSE
            mse = np.mean((arr_a - arr_b) ** 2)
            self.last_mse = mse
            
            # Calculate PSNR
            if mse > 0:
                max_pixel = 255.0
                psnr = 20 * math.log10(max_pixel / math.sqrt(mse))
                self.last_psnr = psnr
            else:
                self.last_psnr = float('inf')
            
            # Calculate difference percentage
            diff_pixels = np.sum(np.abs(arr_a - arr_b) > 10)  # Threshold
            total_pixels = arr_a.shape[0] * arr_a.shape[1] * 3
            self.last_diff_percent = (diff_pixels / total_pixels) * 100
            
            # Create diff image if requested
            show_diff = self.get_param("show_diff", True)
            if show_diff:
                diff = np.abs(arr_a - arr_b).astype(np.uint8)
                diff_img = Image.fromarray(diff, 'RGB')
                buffer = io.BytesIO()
                diff_img.save(buffer, format='PNG')
                result_bytes = buffer.getvalue()
            else:
                # Return the second image
                buffer = io.BytesIO()
                img_b.save(buffer, format='PNG')
                result_bytes = buffer.getvalue()
            
            # Create new packet
            new_pkt = DataPacket(id=packet.id, payload=result_bytes,
                                source_format="image", size_bits=len(result_bytes)*8)
            new_pkt.add_step(self.name, "Compare", len(packet.payload), len(result_bytes),
                           f"MSE={mse:.2f}, PSNR={self.last_psnr:.1f}dB, diff={self.last_diff_percent:.1f}%")
            return new_pkt
            
        except Exception as e:
            packet.add_step(self.name, "Compare", len(packet.payload), len(packet.payload),
                          f"ERROR: {str(e)}")
            return packet