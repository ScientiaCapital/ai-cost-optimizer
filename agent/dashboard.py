#!/usr/bin/env python3
"""CLI Dashboard for Learning Intelligence Visualization - DEPRECATED.

⚠️  THIS FILE IS DEPRECATED - Use the appropriate dashboard version:
    - customer_dashboard.py  (for external/customer use)
    - admin_dashboard.py     (for internal/admin use)

This file now redirects to customer_dashboard.py by default for security.
"""
import sys
import os
import subprocess

def main():
    """Redirect to the appropriate dashboard with deprecation warning."""
    print("\n" + "=" * 70)
    print("  ⚠️  DEPRECATION WARNING")
    print("=" * 70)
    print()
    print("This dashboard.py file is deprecated for security reasons.")
    print()
    print("Please use the appropriate dashboard version:")
    print()
    print("  • customer_dashboard.py  - For external/customer use")
    print("    - Safe to share with customers")
    print("    - Shows only tier labels")
    print()
    print("  • admin_dashboard.py     - For internal/admin use")
    print("    - INTERNAL USE ONLY")
    print("    - Shows actual model names")
    print()
    print("=" * 70)
    print()

    # Ask user which version they want
    while True:
        try:
            print("Which dashboard do you want to run?")
            print()
            print("  1. Customer Dashboard (external-safe)")
            print("  2. Admin Dashboard (internal use only)")
            print("  3. Exit")
            print()
            choice = input("Enter choice (1-3) [1]: ").strip()

            if choice == "" or choice == "1":
                script = "customer_dashboard.py"
                break
            elif choice == "2":
                print()
                print("⚠️  WARNING: Admin dashboard contains competitive intelligence")
                confirm = input("Are you an internal user? (yes/no): ").strip().lower()
                if confirm in ['yes', 'y']:
                    script = "admin_dashboard.py"
                    break
                else:
                    print("\nPlease use customer_dashboard.py instead.")
                    sys.exit(0)
            elif choice == "3":
                print("\nExiting.")
                sys.exit(0)
            else:
                print("\nInvalid choice. Please enter 1, 2, or 3.\n")
        except (KeyboardInterrupt, EOFError):
            print("\n\nCancelled by user.")
            sys.exit(0)

    # Run the selected dashboard
    script_path = os.path.join(os.path.dirname(__file__), script)
    print(f"\nLaunching {script}...\n")

    # Pass through any command-line arguments
    args = sys.argv[1:]
    try:
        result = subprocess.run([sys.executable, script_path] + args)
        sys.exit(result.returncode)
    except FileNotFoundError:
        print(f"Error: {script} not found at {script_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
