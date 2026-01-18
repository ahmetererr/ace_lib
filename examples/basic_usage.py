"""
Basic Usage Example for ACE Core Framework
Demonstrates the core functionality of Adaptive Context Engineering
"""

from ace_core import ACEFramework, ItemType


def main():
    """Basic usage example"""
    
    # Initialize ACE Framework
    print("Initializing ACE Framework...")
    ace = ACEFramework()
    
    # Add initial manual items
    print("\n1. Adding initial manual items...")
    
    ace.add_manual_item(
        content="Always validate user input before processing",
        item_type=ItemType.INSTRUCTION,
        tags=["security", "validation"],
        confidence=0.9
    )
    
    ace.add_manual_item(
        content="Use HTTPS for all API calls",
        item_type=ItemType.CONSTRAINT,
        tags=["security", "api"],
        confidence=0.95
    )
    
    ace.add_manual_item(
        content="Example: Validate email format with regex",
        item_type=ItemType.EXAMPLE,
        tags=["validation", "email"],
        confidence=0.8
    )
    
    print(f"✓ Added {ace.manual.get_statistics()['total_items']} items to manual")
    
    # Get manual statistics
    print("\n2. Manual Statistics:")
    stats = ace.get_statistics()
    print(f"  - Total items: {stats['manual_stats']['total_items']}")
    print(f"  - Active items: {stats['manual_stats']['active_items']}")
    print(f"  - Estimated tokens: {stats['manual_stats']['estimated_tokens']}")
    
    # Execute a complete cycle (without LLM - mock mode)
    print("\n3. Executing ACE cycle (Generate -> Reflect -> Curate)...")
    
    result = ace.execute_cycle(
        task="Process user registration with email validation",
        context="User provides email: test@example.com, password: secure123",
        execution_feedback={
            "success": True,
            "validation_passed": True,
            "email_valid": True,
        },
        success=True
    )
    
    print(f"✓ Cycle completed: {result['cycle_id']}")
    print(f"  - Duration: {result['duration_seconds']:.3f}s")
    print(f"  - Insights generated: {result['reflection']['insights_count']}")
    print(f"  - Updates applied: {result['curation']['summary']['applied']}")
    
    # Get manual context
    print("\n4. Getting manual context for LLM...")
    context = ace.get_manual_context(max_items=5, prioritize_by="usage")
    print(f"  - Context length: {len(context)} characters")
    print(f"  - First 200 chars: {context[:200]}...")
    
    # Search manual
    print("\n5. Searching manual...")
    results = ace.search_manual(query="validation", item_type=ItemType.INSTRUCTION)
    print(f"  - Found {len(results)} items matching 'validation'")
    for item in results:
        print(f"    • {item.item_id[:8]}...: {item.content[:60]}...")
    
    # Get updated statistics
    print("\n6. Updated Statistics:")
    stats = ace.get_statistics()
    print(f"  - Total items: {stats['manual_stats']['total_items']}")
    print(f"  - Total cycles: {stats['total_cycles']}")
    print(f"  - Update history: {stats['update_history_count']}")
    
    # Export state
    print("\n7. Exporting framework state...")
    ace.export_state("ace_state_example.json")
    print("✓ State exported to ace_state_example.json")
    
    print("\n✓ Example completed successfully!")


if __name__ == "__main__":
    main()
