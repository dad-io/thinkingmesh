# 🧠 ThinkingMesh: Symbolic Memory Architecture and Distributed Semantic Mesh Protocol  
### Enabling Agentic AI Systems via Universal Attribute Modeling over Zenoh

---

## 🧬 Abstract

This project introduces a novel semantic and symbolic foundation for distributed intelligent systems, combining:

- A **schema-emergent symbolic memory architecture**
- A **recursive universal attribute model**
- A **thinking mesh protocol** layered on top of **Zenoh** — a real-time, decentralized pub/sub and query fabric

Together, these components establish a substrate for **natively interpretable, queryable, and compressible data flow**, enabling a new class of **agentic and self-reflective AI systems**.

---

## 🎯 Motivation

Modern distributed systems — including industrial automation, IoT fabrics, and LLM-driven agents — lack a **unified semantic substrate** that is:
- **Self-describing**
- **Locally and globally queryable**
- **Symbolically navigable**
- **Robust to schema drift or emergence**

Standards like **JSON**, **RDF**, or **WoT Thing Descriptions** offer partial solutions but:
- Assume external schema or ontology agreement
- Lack recursive symbolic structure
- Are too rigid for emergent intelligence or symbolic compression

This project addresses that gap by offering a fully symbolic, recursive, schema-agnostic substrate using **Universal Attributes** and a distributed mesh protocol atop **Zenoh**.

---

## 📐 Architecture

### 1. Universal Attribute (ATTR) Model

All knowledge is represented as recursive symbolic trees:

```python
# Examples of ATTR structures
temperature: [value: [25.3], unit: [celsius], sensor: [id: [sensor_01]]]
observation: [timestamp: [1625097600], location: [x: [10], y: [20]], data: [temperature: [...]]]
```

Properties:
- **Self-descriptive**: No external schema required
- **Schema-agnostic**: Structure emerges from data
- **Symbolically unifiable**: Patterns can be matched and merged
- **Ideal for inference and compression**

### 2. Symbolic Memory System

Organized as layered memory components:

| Layer | Function |
|-------|----------|
| `episodic_memory` | Stores time-indexed ATTR observations |
| `concept_store` | Generalizes ATTR trees into reusable patterns |
| `working_memory` | Maintains query context + partial bindings |
| `schema_cache` | Stores emergent schemas via pattern folding |
| `query_engine` | Unifies, filters, generalizes, and recalls |

### 3. Thinking Mesh Protocol (over Zenoh)

Agent-level interactions over a real-time key-based fabric. Roles include:
- **Observer** — Publishes observations as ATTR trees
- **Responder** — Matches symbolic queries with local memory
- **Reasoner** — Generalizes, compresses, deduplicates ATTR structures
- **Planner** — Chains symbolic queries toward goal resolution
- **Mediator** — Aligns or transforms schemas across peers

Zenoh provides:
- Real-time pub/sub and query/reply
- Distributed query resolution
- Decentralized mesh-based routing
- Multi-transport support (UDP, TCP, serial, shared memory)

---

## 🧪 Research Contributions

1. **Universal Attribute Model**: A recursive, symbolic generalization of key-value encoding supporting structural reasoning, unification, and schema emergence.

2. **Cognitive Mesh Protocol**: A new class of distributed communication protocol combining symbolic query planning, structural introspection, and local reasoning.

3. **Neural-symbolic Bridge Substrate**: A model substrate for symbolic cognition that can interface with LLMs, serve as prompt scaffolding, or compress raw language into abstract concepts.

4. **Self-organizing Memory**: A memory architecture that generalizes and compresses without requiring central schema or type constraints — akin to human abstraction processes.

---

## 💡 Applications

- Agentic memory for LLM-driven systems
- Federated control networks in industrial edge AI
- Digital twin cognition and symbolic diagnostics
- Sensor graph self-modeling and schema discovery
- Emergent schema consensus across distributed agents

---

## 🛠 Quick Start

```python
from thinkingmesh import ATTR, SymbolicMemory, ThinkingMeshAgent
import asyncio

# Create ATTR structure
observation = ATTR("observation", [
    ATTR("timestamp", [ATTR("value", [1625097600])]),
    ATTR("sensor", [ATTR("id", [ATTR("value", ["temp_01"])])]),
    ATTR("reading", [ATTR("temperature", [ATTR("value", [23.5])])])
])

# Initialize symbolic memory
memory = SymbolicMemory()
memory.store_observation(observation)

# Create mesh agent
agent = ThinkingMeshAgent("observer_node", memory)
await agent.start()

# Publish observation to mesh
await agent.publish_observation(observation)
```

---

## 📚 Related Work

- Semantic Web (RDF, OWL, SHACL)
- Web of Things (WoT TD, JSON-LD)
- Symbolic AI, production systems (SOAR, NARS)
- Knowledge representation (S-expressions, term rewriting)
- Zenoh, DDS, and edge-focused pub/sub routing protocols

---

## 🧪 Academic Directions

- Formalization of ATTR algebra and unification operators
- Graph-theoretic analysis of schema emergence
- LLM grounding and symbolic-to-natural translation
- Reasoning over lossy or symbolic compressions
- Emergence of invariant structures across agents

---

## 📖 License

This work is released under **CC-BY 4.0** / **Public Domain Dedication** as specified in the defensive disclosure. Implementation code is available under **MIT License**.

---

## 📎 Contact

**Samuel Elsner**  
sam.elsner@gmail.com  
GitHub: @dad-io

This is an open research platform — contributions and forks welcome.

