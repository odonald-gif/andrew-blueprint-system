# A simple in-memory dictionary to store user credentials
users = {}

def register_user():
    """Allows a new user to register by providing a username and password."""
    print("\n--- Register ---")
    while True:
        username = input("Enter a new username: ").strip()
        if not username:
            print("Username cannot be empty. Please try again.")
            continue
        if username in users:
            print("Username already exists. Please choose a different one.")
        else:
            break

    while True:
        password = input("Enter a password: ").strip()
        if not password:
            print("Password cannot be empty. Please try again.")
        else:
            break

    users[username] = password
    print(f"User '{username}' registered successfully!")

def login_user():
    """Allows an existing user to log in."""
    print("\n--- Login ---")
    username = input("Enter your username: ").strip()
    password = input("Enter your password: ").strip()

    if username in users and users[username] == password:
        print(f"Welcome, {username}! You have successfully logged in.")
        return True
    else:
        print("Invalid username or password.")
        return False

def main_menu():
    """Displays the main menu and handles user choices."""
    while True:
        print("\n--- Main Menu ---")
        print("1. Register")
        print("2. Login")
        print("3. Exit")
        choice = input("Enter your choice (1-3): ").strip()

        if choice == '1':
            register_user()
        elif choice == '2':
            login_user()
        elif choice == '3':
            print("Exiting the application. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

# Run the main menu when the script is executed
if __name__ == "__main__":
    main_menu()