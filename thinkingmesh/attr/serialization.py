"""
ATTR Serialization Support

Supports multiple serialization formats as specified in the defensive disclosure:
- JSON (human readable)
- MsgPack (compact binary)
- CBOR (standards-based binary)
"""

import json
from typing import Any, Dict, Union
from .core import ATTR, ATTRAtom, ATTRVariable, ATTRValue


class ATTRSerializer:
    """
    Serialization and deserialization for ATTR structures
    
    Supports multiple formats while preserving the recursive symbolic structure
    """
    
    @staticmethod
    def to_dict(attr: ATTR) -> Dict[str, Any]:
        """
        Convert ATTR to dictionary representation
        
        Format:
        {
            "key": "attribute_name",
            "value": {...},
            "type": "attr",
            "timestamp": 1625097600.0
        }
        """
        result = {
            "key": attr.key,
            "type": "attr",
            "timestamp": attr.timestamp
        }
        
        if attr.is_atomic():
            result["value"] = {
                "type": "atom",
                "data": attr.value.value
            }
        
        elif attr.is_variable():
            result["value"] = {
                "type": "variable", 
                "name": attr.value.name
            }
        
        elif attr.is_nested():
            result["value"] = {
                "type": "nested",
                "attributes": [ATTRSerializer.to_dict(nested_attr) for nested_attr in attr.value]
            }
        
        return result
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> ATTR:
        """
        Convert dictionary representation back to ATTR
        """
        key = data["key"]
        timestamp = data.get("timestamp")
        value_data = data["value"]
        
        if value_data["type"] == "atom":
            value = ATTRAtom(value_data["data"])
        
        elif value_data["type"] == "variable":
            value = ATTRVariable(value_data["name"])
        
        elif value_data["type"] == "nested":
            nested_attrs = [ATTRSerializer.from_dict(attr_data) for attr_data in value_data["attributes"]]
            value = nested_attrs
        
        else:
            raise ValueError(f"Unknown value type: {value_data['type']}")
        
        attr = ATTR(key, value)
        if timestamp is not None:
            object.__setattr__(attr, 'timestamp', timestamp)
        
        return attr
    
    @staticmethod
    def to_json(attr: ATTR, indent: int = 2) -> str:
        """
        Serialize ATTR to JSON string
        
        Human-readable format suitable for debugging and interchange
        """
        return json.dumps(ATTRSerializer.to_dict(attr), indent=indent)
    
    @staticmethod
    def from_json(json_str: str) -> ATTR:
        """
        Deserialize ATTR from JSON string
        """
        data = json.loads(json_str)
        return ATTRSerializer.from_dict(data)
    
    @staticmethod
    def to_msgpack(attr: ATTR) -> bytes:
        """
        Serialize ATTR to MsgPack binary format
        
        Compact binary representation for efficient network transmission
        """
        try:
            import msgpack
            return msgpack.packb(ATTRSerializer.to_dict(attr))
        except ImportError:
            raise ImportError("msgpack library required for MsgPack serialization")
    
    @staticmethod
    def from_msgpack(data: bytes) -> ATTR:
        """
        Deserialize ATTR from MsgPack binary format
        """
        try:
            import msgpack
            dict_data = msgpack.unpackb(data, raw=False)
            return ATTRSerializer.from_dict(dict_data)
        except ImportError:
            raise ImportError("msgpack library required for MsgPack deserialization")
    
    @staticmethod
    def to_cbor(attr: ATTR) -> bytes:
        """
        Serialize ATTR to CBOR binary format
        
        Standards-based binary representation (RFC 7049)
        """
        try:
            import cbor2
            return cbor2.dumps(ATTRSerializer.to_dict(attr))
        except ImportError:
            raise ImportError("cbor2 library required for CBOR serialization")
    
    @staticmethod
    def from_cbor(data: bytes) -> ATTR:
        """
        Deserialize ATTR from CBOR binary format
        """
        try:
            import cbor2
            dict_data = cbor2.loads(data)
            return ATTRSerializer.from_dict(dict_data)
        except ImportError:
            raise ImportError("cbor2 library required for CBOR deserialization")
    
    @staticmethod
    def to_compact_string(attr: ATTR) -> str:
        """
        Serialize to compact string representation
        
        Format: key:[nested_key:value,...]
        Example: "car:[engine:[rpm:9500,temp:80]]"
        """
        def serialize_value(value: Union[ATTRValue, list]) -> str:
            if isinstance(value, ATTRAtom):
                if isinstance(value.value, str):
                    return f'"{value.value}"'
                return str(value.value)
            
            elif isinstance(value, ATTRVariable):
                return f"?{value.name}"
            
            elif isinstance(value, list):
                nested = ",".join(ATTRSerializer.to_compact_string(attr) for attr in value)
                return f"[{nested}]"
            
            else:
                return str(value)
        
        return f"{attr.key}:{serialize_value(attr.value)}"
    
    @staticmethod
    def estimate_compression_ratio(attrs: list[ATTR]) -> float:
        """
        Estimate compression ratio for a list of ATTR structures
        
        Useful for evaluating schema-emergent compression effectiveness
        """
        if not attrs:
            return 1.0
        
        # Calculate total size as individual JSON representations
        individual_size = sum(len(ATTRSerializer.to_json(attr, indent=0)) for attr in attrs)
        
        # Calculate size if stored as single JSON array
        combined_data = [ATTRSerializer.to_dict(attr) for attr in attrs]
        combined_size = len(json.dumps(combined_data, separators=(',', ':')))
        
        return individual_size / combined_size if combined_size > 0 else 1.0