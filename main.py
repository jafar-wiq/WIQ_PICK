import streamlit as st
import webbrowser
import pandas as pd
import uuid
import json
from datetime import datetime
import time

# Set page configuration
st.set_page_config(page_title="Link Bucket", layout="wide")

# Initialize session state variables if they don't exist
if 'link_tree' not in st.session_state:
    st.session_state.link_tree = {
        'name': 'Root',
        'id': 'root',
        'type': 'folder',
        'children': []
    }
if 'selected_links' not in st.session_state:
    st.session_state.selected_links = set()
if 'current_path' not in st.session_state:
    st.session_state.current_path = ['root']
if 'expanded_folders' not in st.session_state:
    st.session_state.expanded_folders = set(['root'])
if 'navigate_to_path' not in st.session_state:
    st.session_state.navigate_to_path = None


# Helper functions for tree navigation and manipulation
def get_node_by_path(path):
    """Get node at specified path"""
    node = st.session_state.link_tree
    if path == ['root']:
        return node

    for node_id in path[1:]:
        found = False
        for child in node['children']:
            if child['id'] == node_id:
                node = child
                found = True
                break
        if not found:
            return None
    return node


def add_node(parent_path, node):
    """Add a node to the specified parent path"""
    parent = get_node_by_path(parent_path)
    if parent and parent['type'] == 'folder':
        parent['children'].append(node)
        return True
    return False


def delete_node(node_id, parent_path=None):
    """Delete a node by its ID"""
    if parent_path is None:
        parent_path = st.session_state.current_path

    parent = get_node_by_path(parent_path)
    if parent:
        # Filter out the node to delete
        parent['children'] = [child for child in parent['children'] if child['id'] != node_id]

        # Also remove from selected links if present
        if node_id in st.session_state.selected_links:
            st.session_state.selected_links.remove(node_id)

        # Also remove from expanded folders if it's a folder
        if node_id in st.session_state.expanded_folders:
            st.session_state.expanded_folders.remove(node_id)

        return True
    return False


def get_all_links():
    """Get all links from the tree (for select all functionality)"""
    all_links = []

    def traverse(node):
        if node['type'] == 'link':
            all_links.append(node)
        elif node['type'] == 'folder':
            for child in node['children']:
                traverse(child)

    traverse(st.session_state.link_tree)
    return all_links


def count_all_folders():
    """Count all folders in the tree"""
    folder_count = 0

    def traverse(node):
        nonlocal folder_count
        if node['type'] == 'folder':
            for child in node['children']:
                if child['type'] == 'folder':
                    folder_count += 1
                    traverse(child)

    traverse(st.session_state.link_tree)
    return folder_count


def get_breadcrumb_paths(path):
    """Get paths for breadcrumb navigation"""
    paths = []
    for i in range(len(path)):
        paths.append(path[:i + 1])
    return paths


def get_breadcrumb_names(path):
    """Get names for breadcrumb navigation"""
    names = ['Root']
    current = st.session_state.link_tree

    for node_id in path[1:]:
        for child in current['children']:
            if child['id'] == node_id:
                names.append(child['name'])
                current = child
                break

    return names


# UI Functions
def add_folder():
    """Add a new folder to current path"""
    if st.session_state.new_folder_name:
        folder = {
            'id': str(uuid.uuid4()),
            'name': st.session_state.new_folder_name,
            'type': 'folder',
            'children': [],
            'date_added': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        if add_node(st.session_state.current_path, folder):
            st.session_state.new_folder_name = ""


def add_link():
    """Add a new link to current path"""
    if st.session_state.new_link and st.session_state.link_name:
        # Ensure link has proper format
        link = st.session_state.new_link
        if not link.startswith(('http://', 'https://')):
            link = 'https://' + link

        # Create link entry with unique ID
        link_entry = {
            'id': str(uuid.uuid4()),
            'name': st.session_state.link_name,
            'url': link,
            'type': 'link',
            'date_added': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        if add_node(st.session_state.current_path, link_entry):
            st.session_state.new_link = ""
            st.session_state.link_name = ""


def navigate_to(path):
    """Navigate to a specific path"""
    st.session_state.current_path = path
    # Check if we need to expand any folders in the path
    for i in range(len(path)):
        if i > 0:  # Skip root
            st.session_state.expanded_folders.add(path[i])


def set_navigate_path(path):
    """Set the navigation path for next rerun"""
    st.session_state.navigate_to_path = path
    st.rerun()


def toggle_folder_expansion(folder_id):
    """Toggle folder expansion state"""
    if folder_id in st.session_state.expanded_folders:
        st.session_state.expanded_folders.remove(folder_id)
    else:
        st.session_state.expanded_folders.add(folder_id)


def select_all_links():
    """Select all links in the tree"""
    all_links = get_all_links()
    st.session_state.selected_links = {link['id'] for link in all_links}


def deselect_all_links():
    """Deselect all links"""
    st.session_state.selected_links = set()


def open_selected_links():
    """Open all selected links"""
    if st.session_state.selected_links:
        all_links = get_all_links()
        for link in all_links:
            if link['id'] in st.session_state.selected_links:
                webbrowser.open_new_tab(link['url'])
                # Small delay to prevent browser from blocking multiple windows
                time.sleep(0.3)
        return True
    return False


# Check if we need to navigate
if st.session_state.navigate_to_path is not None:
    navigate_to(st.session_state.navigate_to_path)
    st.session_state.navigate_to_path = None


# Recursive function to render the tree
def render_tree(node, path, level=0):
    if node['type'] == 'folder':
        is_expanded = node['id'] in st.session_state.expanded_folders
        indent = "　" * level  # Use full-width space for better alignment

        # Create columns for the folder
        cols = st.columns([0.05, 0.8, 0.15])

        with cols[0]:
            # Expand/collapse button
            icon = "📂" if not is_expanded else "📂"  # You could use different icons but this works
            if st.button(icon, key=f"toggle_{node['id']}", help="Expand/collapse"):
                toggle_folder_expansion(node['id'])
                st.rerun()

        with cols[1]:
            # Folder name (clickable to navigate)
            if node['id'] != 'root':  # Don't need to navigate to root
                if st.button(
                        f"{indent}{node['name']}/",
                        key=f"folder_{node['id']}",
                        use_container_width=True,
                        type="secondary"
                ):
                    set_navigate_path(path + [node['id']])
            else:
                st.markdown(f"**{node['name']}**")

        with cols[2]:
            # Delete button (don't show for root)
            if node['id'] != 'root':
                if st.button(
                        "🗑️",
                        key=f"delete_{node['id']}",
                        help="Delete this folder and all contents"
                ):
                    delete_node(node['id'], path[:-1] if len(path) > 1 else path)
                    st.rerun()

        # If expanded, render children
        if is_expanded:
            for child in node['children']:
                render_tree(child, path + [child['id']], level + 1)

    elif node['type'] == 'link':
        indent = "　" * (level + 1)  # Indent links more than their parent folders

        # Create columns for the link
        cols = st.columns([0.05, 0.8, 0.15])

        with cols[0]:
            # Checkbox for selection
            is_selected = node['id'] in st.session_state.selected_links
            if st.checkbox(
                    "",
                    value=is_selected,
                    key=f"checkbox_{node['id']}",
            ):
                if node['id'] not in st.session_state.selected_links:
                    st.session_state.selected_links.add(node['id'])
            else:
                if node['id'] in st.session_state.selected_links:
                    st.session_state.selected_links.remove(node['id'])

        with cols[1]:
            # Link name (clickable to open)
            if st.button(
                    f"{indent}🔗 {node['name']}",
                    key=f"link_{node['id']}",
                    help=node['url'],
                    use_container_width=True
            ):
                webbrowser.open_new_tab(node['url'])

        with cols[2]:
            # Delete button
            if st.button(
                    "🗑️",
                    key=f"delete_{node['id']}",
                    help="Delete this link"
            ):
                delete_node(node['id'], path[:-1] if len(path) > 1 else path)
                st.rerun()


# Main App UI
st.title("📚 WIQ Picker")

# Sidebar for adding new links/folders
with st.sidebar:
    st.header("Add to Current Folder")

    # Show current path
    current_node = get_node_by_path(st.session_state.current_path)
    if current_node:
        st.info(f"Current folder: {current_node['name']}")

    # Add folder section
    st.subheader("Add New Folder")
    st.text_input("Folder Name", key="new_folder_name", placeholder="e.g. Work")
    st.button("Create Folder", on_click=add_folder)

    st.divider()

    # Add link section
    st.subheader("Add New Link")
    st.text_input("Link Name", key="link_name", placeholder="e.g. Google")
    st.text_input("URL", key="new_link", placeholder="e.g. google.com")
    st.button("Add Link", on_click=add_link)

# Main area for link management
col1, col2 = st.columns([3, 1])

with col1:
    # Breadcrumb navigation
    st.subheader("Link Tree")

    # Create breadcrumb navigation
    breadcrumb_names = get_breadcrumb_names(st.session_state.current_path)
    breadcrumb_paths = get_breadcrumb_paths(st.session_state.current_path)

    # Create a horizontal layout for breadcrumbs
    bc_cols = st.columns(len(breadcrumb_names) * 2 - 1)

    for i, (name, path) in enumerate(zip(breadcrumb_names, breadcrumb_paths)):
        # Add breadcrumb item
        with bc_cols[i * 2]:
            # Make each breadcrumb part clickable
            if i < len(breadcrumb_names) - 1 or len(st.session_state.current_path) == 1:
                if st.button(name, key=f"breadcrumb_{i}"):
                    set_navigate_path(path)
            else:
                st.markdown(f"**{name}**")

        # Add separator (except after the last item)
        if i < len(breadcrumb_names) - 1:
            with bc_cols[i * 2 + 1]:
                st.write(" > ")

    st.divider()

    # Render the current folder contents
    current_node = get_node_by_path(st.session_state.current_path)
    if current_node:
        if not current_node['children']:
            st.info(f"This folder is empty. Add links or folders using the sidebar!")
        else:
            # Display folder contents
            for child in current_node['children']:
                render_tree(child, st.session_state.current_path, 0)
    else:
        st.error("Invalid path. Navigating to root.")
        set_navigate_path(['root'])

with col2:
    st.subheader("Actions")

    # Select/Deselect all buttons
    col_select, col_deselect = st.columns(2)
    with col_select:
        st.button("Select All", on_click=select_all_links, use_container_width=True)
    with col_deselect:
        st.button("Deselect All", on_click=deselect_all_links, use_container_width=True)

    # Connect button
    if st.session_state.selected_links:
        if st.button(
                f"🔗 Connect to Selected ({len(st.session_state.selected_links)})",
                on_click=open_selected_links,
                use_container_width=True,
                type="primary"
        ):
            st.balloons()
    else:
        st.button(
            "🔗 Connect (Select links first)",
            disabled=True,
            use_container_width=True
        )

    # Statistics
    st.divider()
    st.subheader("Statistics")

    all_links = get_all_links()
    folder_count = count_all_folders()

    st.metric("Total Folders", folder_count)
    st.metric("Total Links", len(all_links))
    st.metric("Selected Links", len(st.session_state.selected_links))

# Footer
st.divider()
st.caption("Link Bucket - Organize and navigate to your favorite links")