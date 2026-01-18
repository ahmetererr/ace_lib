# ACE Core: Adaptive Context Engineering Framework

**Preventing Context Collapse in Large Language Model (LLM) Agents via Incremental Updates**

## Overview

ACE Core is a Python library that implements the Adaptive Context Engineering (ACE) framework, designed to overcome fundamental architectural limitations in knowledge-intensive LLM agents. The framework addresses **Context Collapse** and **Concision Bias** by treating agent context as an **Evolving Manual** - a structured, memory object that manages knowledge through incremental updates rather than monolithic rewriting.

## Key Features

### 🔄 **Evolving Manual**
- Structured, versioned knowledge base
- Incremental growth without rewriting
- Item-based organization with metadata tracking
- Automatic versioning and dependency tracking

### 🤖 **Modular Agent Architecture**
- **Generator**: Uses the Evolving Manual to produce reasoning and code
- **Reflector**: Analyzes execution traces and distills insights
- **Curator**: Synthesizes reflections into structured updates

### ⚡ **Incremental Delta Updates**
- Prevents Context Collapse through structured updates
- Deterministic merging logic (no LLM compression)
- Localized, traceable changes
- Batch update support

### 📊 **Dynamic Metadata Management**
- Comprehensive tracking of item provenance
- Usage statistics and confidence scores
- Dependency graphs
- Search and filtering capabilities

## Installation

### Option 1: Install from GitHub (Recommended)

```bash
pip install git+https://github.com/ahmetererr/ace_lib.git
```

### Option 2: Clone and Install

```bash
git clone https://github.com/ahmetererr/ace_lib.git
cd ace_lib
pip install -r requirements.txt
pip install -e .
```

### Option 3: Direct Import (Development)

If you have the project locally and want to use it in another project:

```bash
# In your other project
pip install -e /path/to/ace-core
```

Then import in your code:
```python
from ace_core import ACEFramework, ItemType
```

## Quick Start

```python
from ace_core import ACEFramework, ItemType

# Initialize framework
ace = ACEFramework()

# Add initial manual items
ace.add_manual_item(
    content="Always validate user input before processing",
    item_type=ItemType.INSTRUCTION,
    tags=["security", "validation"],
    confidence=0.9
)

# Execute a complete cycle: Generate -> Reflect -> Curate
result = ace.execute_cycle(
    task="Process user registration data",
    context="User provides email and password",
    execution_feedback={"success": True, "validation_passed": True},
    success=True
)

# Access results
print(f"Generated: {result['generation']['response']}")
print(f"Insights: {len(result['reflection']['insights'])}")
print(f"Applied updates: {result['curation']['summary']['applied']}")

# Get manual context for LLM
context = ace.get_manual_context(max_items=10, prioritize_by="usage")
```

## Architecture

### Evolving Manual Structure

```
ManualItem
├── content: str
├── item_id: str
├── item_type: ItemType (INSTRUCTION, INSIGHT, PATTERN, etc.)
└── metadata: Metadata
    ├── created_at, updated_at
    ├── created_by (Generator/Reflector/Curator)
    ├── version, status
    ├── usage_count, confidence_score
    ├── tags, dependencies
    └── custom_fields
```

### Agent Workflow

```
Task Input
    ↓
[Generator] → Uses Manual → Generates Response
    ↓
Execution Feedback
    ↓
[Reflector] → Analyzes Trace → Creates Insights (DeltaUpdate)
    ↓
[Curator] → Synthesizes → Applies Incremental Updates
    ↓
Updated Manual
```

## Core Components

### ACEFramework
Main orchestrator class that coordinates all components.

```python
ace = ACEFramework(llm_client=your_llm_client)

# Execute complete cycle
result = ace.execute_cycle(task, context, feedback, success)

# Or use individual phases
generation = ace.generate_only(task)
insights = ace.reflect_only(generation, feedback, success)
curation = ace.curate_only(insights)
```

### EvolvingManual
The core knowledge storage object.

```python
manual = EvolvingManual()

# Add items
item_id = manual.add_item(item, metadata)

# Search
items = manual.get_items_by_type(ItemType.INSTRUCTION)
items = manual.get_items_by_tag("security")

# Get context string for LLM
context = manual.to_context_string(max_items=10)
```

### MetadataManager
Tracks metadata for all manual items.

```python
manager = MetadataManager()

# Get statistics
stats = manager.get_statistics()

# Search
items = manager.search_by_type(ItemType.INSIGHT)
items = manager.get_most_used(limit=10)
```

### DeltaUpdate
Represents incremental changes to the manual.

```python
delta = DeltaUpdate(
    action="add",
    item_type=ItemType.INSIGHT,
    content="New insight content",
    created_by="Reflector",
    confidence=0.8,
    tags=["pattern", "reflection"]
)
```

## Advanced Usage

### Custom LLM Client Integration

```python
class CustomLLMClient:
    def generate(self, prompt, max_tokens=2000):
        # Your LLM API call
        return response
    
    def complete(self, prompt):
        # Alternative interface
        return response

ace = ACEFramework(llm_client=CustomLLMClient())
```

### Persistent Storage

```python
# Save framework state
ace.export_state("ace_state.json")

# Load framework state
ace = ACEFramework.load_state("ace_state.json", llm_client=client)
```

### Manual Review and Curation

```python
# Review manual items
review_result = ace.review_manual(
    focus_areas=["security", "validation"],
    max_reviews=20
)

# Search manual
results = ace.search_manual(
    query="user input",
    item_type=ItemType.INSTRUCTION,
    tags=["security"]
)
```

## Item Types

- **INSTRUCTION**: Guidelines and procedures
- **INSIGHT**: Learned patterns and lessons
- **PATTERN**: Reusable code/behavior patterns
- **EXAMPLE**: Concrete examples
- **CONSTRAINT**: Restrictions and rules
- **REFINEMENT**: Improvements to existing items

## Preventing Context Collapse

ACE prevents Context Collapse through:

1. **Incremental Updates**: Additions instead of full rewrites
2. **Deterministic Merging**: No LLM compression of existing content
3. **Versioned History**: Track all changes without loss
4. **Structured Organization**: Item-based storage with metadata
5. **Prioritization**: Smart selection of items for context

## Requirements

- Python 3.8+
- See `requirements.txt` for dependencies

## License

This project is part of the Capstone Project at [Your University].

## References

- ACE Architecture Paper: [arXiv:2510.04618](https://arxiv.org/pdf/2510.04618)
- Context Collapse: Non-linear degradation of knowledge in long-context LLMs
- Incremental Delta Updates: Structured updates preventing information loss

## Contributing

This is a research project. For questions or contributions, please contact the project maintainer.

## Example Use Case

```python
from ace_core import ACEFramework, ItemType

# Initialize
ace = ACEFramework(llm_client=openai_client)

# Add initial knowledge
ace.add_manual_item(
    content="Use HTTPS for all API calls",
    item_type=ItemType.CONSTRAINT,
    tags=["security", "api"]
)

# Run multiple cycles
for task in task_list:
    result = ace.execute_cycle(
        task=task,
        execution_feedback=execute_task(task),
        success=True
    )
    print(f"Cycle completed: {result['cycle_id']}")

# Review accumulated knowledge
stats = ace.get_statistics()
print(f"Manual items: {stats['manual_stats']['total_items']}")
print(f"Total cycles: {stats['total_cycles']}")
```
