import streamlit as st
import os
import webbrowser
import shutil
from pathlib import Path

# Define the base directory for the link folders. Use a hidden directory.
BASE_DIR = Path(".multi_link_app_data")

# Ensure the base directory exists
if not BASE_DIR.exists():
    BASE_DIR.mkdir(parents=True, exist_ok=True)


def create_folder(folder_name):
    """
    Creates a new folder within the base directory.

    Args:
        folder_name (str): The name of the folder to create.
    """
    folder_path = BASE_DIR / folder_name
    if not folder_path.exists():
        folder_path.mkdir(parents=True, exist_ok=True)
        st.success(f"Folder '{folder_name}' created successfully!")
    else:
        st.warning(f"Folder '{folder_name}' already exists.")
    return folder_path  # Return the path to the created folder


def add_link_to_folder(folder_name, link_name, link_url):
    """
    Adds a link to a specified folder. The link is stored in a text file.

    Args:
        folder_name (str): The name of the folder.
        link_name (str): The name of the link.
        link_url (str): The URL of the link.
    """
    folder_path = BASE_DIR / folder_name
    if not folder_path.exists():
        st.error(f"Folder '{folder_name}' does not exist.")
        return

    link_file_path = folder_path / f"{link_name.strip()}.txt"
    if not link_file_path.exists():
        try:
            with open(link_file_path, "w") as f:
                f.write(link_url.strip())  # Strip to remove extra spaces
            st.success(f"Link '{link_name}' added to folder '{folder_name}' successfully!")
        except Exception as e:
            st.error(f"Error adding link: {e}")
    else:
        st.warning(f"Link '{link_name}' already exists in folder '{folder_name}'.")


def read_links_from_folder(folder_name):
    """
    Reads links from a specified folder.

    Args:
        folder_name (str): The name of the folder.

    Returns:
        dict: A dictionary of link names and URLs, or None if the folder doesn't exist or is empty.
    """
    folder_path = BASE_DIR / folder_name
    if not folder_path.exists():
        st.error(f"Folder '{folder_name}' does not exist.")
        return None

    links = {}
    for file_path in folder_path.glob("*.txt"):
        try:
            with open(file_path, "r") as f:
                link_url = f.read().strip()
            links[file_path.stem] = link_url
        except Exception as e:
            st.error(f"Error reading link from {file_path}: {e}")
    return links if links else None


def open_links(links):
    """
    Opens multiple links in the default web browser.

    Args:
        links (dict): A dictionary of link names and URLs.
    """
    if links:
        for link_name, link_url in links.items():
            try:
                webbrowser.open_new_tab(link_url)
                st.success(f"Opened link: {link_name} - {link_url}")
            except Exception as e:
                st.error(f"Error opening link {link_name}: {e}")
    else:
        st.info("No links to open.")


def delete_folder(folder_name):
    """
    Deletes a folder and all its contents.

    Args:
        folder_name (str): The name of the folder to delete.
    """
    folder_path = BASE_DIR / folder_name
    if folder_path.exists():
        try:
            shutil.rmtree(folder_path)
            st.success(f"Folder '{folder_name}' and its contents deleted successfully!")
        except Exception as e:
            st.error(f"Error deleting folder '{folder_name}': {e}")
    else:
        st.warning(f"Folder '{folder_name}' does not exist.")


def display_app():
    """
    Main function to run the Streamlit app.
    """
    st.title("Multi-Link Opener")

    # Sidebar for folder management
    st.sidebar.header("Folder Management")
    new_folder_name = st.sidebar.text_input("New Folder Name:")
    if st.sidebar.button("Create Folder"):
        create_folder(new_folder_name)

    folder_to_delete = st.sidebar.text_input("Folder to Delete:")
    if st.sidebar.button("Delete Folder"):
        delete_folder(folder_to_delete)

    # Sidebar for link management
    st.sidebar.header("Link Management")
    existing_folders = [d.name for d in BASE_DIR.iterdir() if d.is_dir()]  # Get existing folder names
    folder_name = st.sidebar.selectbox("Folder Name:", existing_folders) # Use selectbox
    link_name = st.sidebar.text_input("Link Name:")
    link_url = st.sidebar.text_input("Link URL:")
    if st.sidebar.button("Add Link"):
        add_link_to_folder(folder_name, link_name, link_url)

    # Main area for displaying and opening links
    st.header("Open Links")
    folder_name_to_open = st.selectbox(
        "Select a folder to open links from:",
        [d.name for d in BASE_DIR.iterdir() if d.is_dir()],
    )
    if folder_name_to_open:
        links_to_open = read_links_from_folder(folder_name_to_open)
        if links_to_open:
            st.write(f"Links in folder '{folder_name_to_open}':")
            selected_links = []  # List to store selected links
            for link_name, link_url in links_to_open.items():
                # Add a checkbox for each link.  Use the link name as the key.
                checked = st.checkbox(f"{link_name} - [{link_url}]({link_url})", key=link_name)
                if checked:
                    selected_links.append((link_name, link_url))  # Add selected links to the list

            if st.button(f"Open Selected Links in '{folder_name_to_open}'"):
                open_links(dict(selected_links))  # Convert the list back to a dictionary before opening
        else:
            st.info(f"No links found in folder '{folder_name_to_open}'.")
    else:
        st.info("Please create a folder first.")


if __name__ == "__main__":
    display_app()
