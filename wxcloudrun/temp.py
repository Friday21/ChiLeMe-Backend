import os
import heapq


def get_folder_size(folder):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            # Skip if it is a symbolic link
            if not os.path.islink(file_path):
                total_size += os.path.getsize(file_path)
    return total_size


def find_top_n_largest_leaf_folders(start_path, n=10):
    largest_folders = []

    for dirpath, dirnames, filenames in os.walk(start_path):
        if not dirnames:  # If there are no subdirectories, it's a leaf folder
            folder_size = get_folder_size(dirpath)
            # Use a heap to keep track of the top N largest folders
            if len(largest_folders) < n:
                heapq.heappush(largest_folders, (folder_size, dirpath))
            else:
                heapq.heappushpop(largest_folders, (folder_size, dirpath))

    # Sort the largest folders by size in descending order
    largest_folders.sort(reverse=True, key=lambda x: x[0])
    return largest_folders


if __name__ == "__main__":
    start_path = 'C:\\'
    top_folders = find_top_n_largest_leaf_folders(start_path, 10)
    for size, folder in top_folders:
        print(f"Folder: {folder}, Size: {size / (1024 ** 3):.2f} GB")
