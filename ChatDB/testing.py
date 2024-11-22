from typing import List, Optional
from collections import deque
class TreeNode:
    def __init__(self, val = 0, left = None, right = None):
        self.val = val
        self.left = left
        self.right = right
class Solution:
    def preOrder(self, root: Optional[TreeNode]) -> List[int]:
        # C L R
        q = deque()
        res =[]
        q.append(root)
        while q:
            curr = q.popleft()
            res.append(curr.val)
           
            # print("value popped in order ", curr.val)
            if curr.left:
                q.append(curr.left)
                # print("did i add 9 first?", curr.left.val)
            if curr.right:
                q.append(curr.right)
        return res
    
# Helper function to build the binary tree from a list
def build_tree(nodes):
    if not nodes:
        return None
    root = TreeNode(nodes[0])
    queue = [root]
    i = 1
    while i < len(nodes):
        current = queue.pop(0)
        if nodes[i] is not None:
            current.left = TreeNode(nodes[i])
            queue.append(current.left)
        i += 1
        if i < len(nodes) and nodes[i] is not None:
            current.right = TreeNode(nodes[i])
            queue.append(current.right)
        i += 1
    return root

# Main function to test the Solution with the given input
def main():
    # Input binary tree as a list
    nodes = [3, 9, 20, None, None, 15, 7]
    
    # Build the binary tree from the list
    root = build_tree(nodes)
    
    # Create a Solution object and call the preOrder function
    solution = Solution()
    result = solution.preOrder(root)
    
    # Print the result
    print("Pre-order Traversal of the Tree:", result)

# Call the main function
main()
    
        

