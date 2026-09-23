"""Create an admin user with superuser privileges."""

import getpass
import sys
from argparse import ArgumentParser


def add_arguments(parser: ArgumentParser) -> None:
    """Add command line arguments."""
    parser.add_argument(
        "--username",
        help="Username for the admin user"
    )
    parser.add_argument(
        "--email",
        help="Email address for the admin user"
    )
    parser.add_argument(
        "--password",
        help="Password (will prompt if not provided)"
    )
    parser.add_argument(
        "--no-input",
        action="store_true",
        help="Don't prompt for input, use command-line arguments only"
    )


def execute(args) -> None:
    """Create the admin user."""
    from fastframe.contrib.auth import get_user_model
    from fastframe.core.bootstrap import bootstrap
    from fastframe.db.session import session_scope
    
    bootstrap()
    User = get_user_model()

    from fastframe.db.engine import get_engine
    from fastframe.models import Model

    Model.metadata.create_all(bind=get_engine())
    
    # Get username
    username = getattr(args, 'username', None)
    if not username and not getattr(args, 'no_input', False):
        username = input("Username: ")
    if not username:
        print("Error: Username is required", file=sys.stderr)
        sys.exit(1)
    
    # Get email
    email = getattr(args, 'email', None)
    if not email and not getattr(args, 'no_input', False):
        email = input("Email: ")
    if not email:
        print("Error: Email is required", file=sys.stderr)
        sys.exit(1)
    
    # Get password
    password = getattr(args, 'password', None)
    if not password and not getattr(args, 'no_input', False):
        password = getpass.getpass("Password: ")
        password2 = getpass.getpass("Password (again): ")
        if password != password2:
            print("Error: Passwords don't match", file=sys.stderr)
            sys.exit(1)
    if not password:
        print("Error: Password is required", file=sys.stderr)
        sys.exit(1)
    
    try:
        with session_scope() as session:
            # Check if user already exists
            existing_user = session.query(User).filter_by(username=username).first()
            if existing_user:
                print(f"Error: User '{username}' already exists", file=sys.stderr)
                sys.exit(1)
            
            # Create the admin user
            user = User(
                username=username,
                email=email,
                is_active=True,
                user_data={
                    "admin_access": True,
                    "superuser": True,
                    "permissions": ["*"],
                    "created_by": "createadminuser command"
                }
            )
            user.set_password(password)
            
            session.add(user)
            session.commit()
            
            print(f"Admin user '{username}' created successfully!")
            print("The user has:")
            print("  - Admin access: Yes")
            print("  - Superuser privileges: Yes")
            print("  - All permissions: Yes")
            
    except Exception as e:
        print(f"Error creating admin user: {e}", file=sys.stderr)
        sys.exit(1)