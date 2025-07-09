# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ThinkingMesh implements a novel symbolic memory architecture and distributed semantic mesh protocol. It combines recursive Universal Attribute (ATTR) modeling with schema-emergent memory over Zenoh for distributed AI reasoning.

## Architecture

### Core Components (IMPLEMENTED)
- **ATTR Model** (`thinkingmesh/attr/`): Recursive symbolic structures with formal algebra
- **Symbolic Memory** (`thinkingmesh/memory/`): Multi-layer memory (episodic, conceptual, schematic) 
- **Query Engine**: Unified symbolic query processing with unification

### Missing Components (TO IMPLEMENT)
- **Mesh Protocol** (`thinkingmesh/mesh/`): Zenoh-based distributed reasoning
- **Agent System** (`thinkingmesh/agents/`): Agent roles and lifecycle management

## Common Development Commands

### Setup and Installation
```bash
# Install core dependencies
pip install -e .

# Install development dependencies  
pip install -e ".[dev]"
```

### Code Quality (NEEDS IMPLEMENTATION)
```bash
# Run tests (need to create test suite)
pytest tests/

# Code formatting
black thinkingmesh/
ruff check thinkingmesh/

# Type checking
mypy thinkingmesh/
```

## Key Components

### Universal Attribute (ATTR) Model
- `ATTR`: Recursive symbolic structure `attribute: [attribute[...]]`
- `ATTRAlgebra`: Formal operators (∪, ⊆, ≈, .)
- `ATTRPattern`: Pattern matching with variable binding
- `ATTRQuery`: Symbolic queries with conditions

### Symbolic Memory Architecture  
- `EpisodicMemory`: Time-indexed ATTR observations
- `ConceptStore`: Generalized patterns and concept formation
- `WorkingMemory`: Active query context and variable bindings
- `SchemaCache`: Emergent schemas via pattern folding
- `QueryEngine`: Unified query processing across memory layers
- `SymbolicMemory`: High-level orchestrator

### Example Usage
```python
from thinkingmesh import ATTR, SymbolicMemory

# Create observation
obs = ATTR("temperature", [
    ATTR("value", 25.3),
    ATTR("sensor", "temp_01"),
    ATTR("location", "room_a")
])

# Store in memory
memory = SymbolicMemory()
memory.store_observation(obs)

# Query with pattern
from thinkingmesh.attr import ATTRPattern, attr_var
pattern = ATTRPattern(ATTR("temperature", [
    ATTR("value", attr_var("temp")),
    ATTR("sensor", attr_var("sensor_id"))
]))

results = memory.query(pattern)
```

## Critical Next Steps

### 1. Fix Code Quality Issues
- Remove unused variables in `query.py` (lines 108, 114, 121, etc.)
- Add proper exception handling
- Implement comprehensive test suite

### 2. Implement Zenoh Mesh Protocol
- `ThinkingMeshAgent` base class
- Agent roles: Observer, Responder, Reasoner, Planner, Mediator
- Zenoh keyspace: `/ATTR/{node}/observation`, `/ATTR/{node}/query`
- Distributed query resolution

### 3. Security and Production Readiness
- Access control for ATTR structures
- Secure query parsing (prevent injection)
- Network authentication
- Performance benchmarking

## Innovation Status

**Core Contributions (COMPLETE):**
- Recursive universal attribute model with formal symbolic algebra
- Schema-emergent compression and memory architecture
- Multi-layer symbolic memory system

**Missing for Full System:**
- Distributed mesh protocol over Zenoh
- Agent-based reasoning network
- Production security and testing

## Research Significance

This implements novel approaches to:
- Schema-free symbolic knowledge representation
- Distributed symbolic reasoning without centralized ontology
- Self-organizing memory with emergent compression
- Neural-symbolic bridge for LLM grounding