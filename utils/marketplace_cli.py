"""
Marketplace CLI - Command-line interface for viewing marketplace data.
Run this while agents are running to see real-time marketplace state.
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.marketplace import marketplace


def display_header():
    """Display CLI header."""
    print("\n" + "=" * 70)
    print(" " * 15 + "AI ECONOMY PROTOCOL - MARKETPLACE")
    print("=" * 70)


def display_stats():
    """Display marketplace statistics."""
    stats = marketplace.get_stats()
    print("\n📊 MARKETPLACE STATISTICS")
    print("-" * 70)
    print(f"Total Agents:        {stats['total_agents']}")
    print(f"Total Services:      {stats['total_services']}")
    print(f"Active Services:     {stats['active_services']}")
    print(f"Categories:          {stats['categories']}")
    print(f"Total Transactions:  {stats['total_transactions']}")


def display_agents():
    """Display all registered agents."""
    agents = marketplace.get_all_agents()
    
    print("\n👥 REGISTERED AGENTS")
    print("-" * 70)
    
    if not agents:
        print("No agents registered yet.")
        return
    
    for agent in agents:
        print(f"\n  Name: {agent.agent_name}")
        print(f"  Address: {agent.agent_address}")
        print(f"  Type: {agent.agent_type}")
        print(f"  Services Offered: {len(agent.services_offered)}")
        print(f"  Reputation: {agent.reputation_score:.2f}")
        print(f"  Transactions: {agent.total_transactions}")
        print(f"  Registered: {agent.registered_at.strftime('%Y-%m-%d %H:%M:%S')}")


def display_services():
    """Display all available services."""
    services = marketplace.get_all_services()
    
    print("\n🛍️  AVAILABLE SERVICES")
    print("-" * 70)
    
    if not services:
        print("No services available yet.")
        return
    
    # Group by category
    categories = {}
    for service in services:
        if service.category not in categories:
            categories[service.category] = []
        categories[service.category].append(service)
    
    for category, cat_services in categories.items():
        print(f"\n  📁 {category}")
        for service in cat_services:
            print(f"    • {service.service_name}")
            print(f"      Price: {service.price_sol} SOL")
            print(f"      Provider: {service.provider_name}")
            print(f"      Description: {service.description}")
            print()


def display_service_search():
    """Interactive service search."""
    print("\n🔍 SERVICE SEARCH")
    print("-" * 70)
    
    categories = marketplace.get_categories()
    if categories:
        print(f"Available categories: {', '.join(categories)}")
        category = input("Enter category (or press Enter for all): ").strip()
        if not category:
            category = None
    else:
        category = None
    
    max_price_input = input("Enter max price in SOL (or press Enter for no limit): ").strip()
    max_price = float(max_price_input) if max_price_input else None
    
    results = marketplace.search_services(category=category, max_price=max_price)
    
    print(f"\nFound {len(results)} services:")
    for service in results:
        print(f"  • {service.service_name} - {service.price_sol} SOL")
        print(f"    Provider: {service.provider_name}")
        print(f"    Category: {service.category}")


def display_menu():
    """Display main menu."""
    print("\n📋 MENU")
    print("-" * 70)
    print("1. View Statistics")
    print("2. View All Agents")
    print("3. View All Services")
    print("4. Search Services")
    print("5. Refresh Display")
    print("6. Export to JSON")
    print("0. Exit")
    print("-" * 70)


def export_marketplace():
    """Export marketplace data to JSON file."""
    json_data = marketplace.export_to_json()
    filename = f"marketplace_export_{int(time.time())}.json"
    
    with open(filename, 'w') as f:
        f.write(json_data)
    
    print(f"\n✓ Marketplace data exported to: {filename}")


def main():
    """Main CLI loop."""
    while True:
        display_header()
        display_stats()
        display_menu()
        
        choice = input("\nEnter your choice: ").strip()
        
        if choice == "1":
            display_stats()
            input("\nPress Enter to continue...")
        elif choice == "2":
            display_agents()
            input("\nPress Enter to continue...")
        elif choice == "3":
            display_services()
            input("\nPress Enter to continue...")
        elif choice == "4":
            display_service_search()
            input("\nPress Enter to continue...")
        elif choice == "5":
            continue
        elif choice == "6":
            export_marketplace()
            input("\nPress Enter to continue...")
        elif choice == "0":
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid choice. Please try again.")
            time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
        sys.exit(0)
