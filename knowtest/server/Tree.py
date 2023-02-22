from typing import Union
import uuid
import os
import sys

module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
    sys.path.append(module_path)

from knowledge.knbase import KnowledgeBase
from server.StateStack import StateStack

class Node:
    def __init__(self, name: str, parent_id: str, node_id: Union[str, None]=None, tags=[], isOpen: bool=False, isHighlighted: bool=False):
        self.name = name

        if node_id is None:
            self.id = str(uuid.uuid4())
        else:
            self.id = node_id

        self.parent_id = parent_id
        self.tags = tags
        self.isOpen = isOpen
        self.isHighlighted = isHighlighted
        self.children = []
        self.process_node()
    
    def process_node(self) -> None:
        self.name = self.name.capitalize()
        self.tags = [tag.replace('\n', "") for tag in self.tags if tag not in ["", "\n", " "]]
        self.isHighlighted = self.strToBool(self.isHighlighted)
        self.isOpen = self.strToBool(self.isOpen)

    def strToBool(self, string: str) -> bool:
        if type(string) == bool:
            return string
        string = string.lower()
        if string in ["true", "t", "yes", "y", "1"]:
            return True
        elif string in ["false", "f", "no", "n", "0"]:
            return False
        else:
            # raise ValueError("Unable to convert \"{}\" to bool".format(string))
            return True

    def generate_new_id(self) -> None:
        self.id = str(uuid.uuid4())

    def __repr__(self) -> str:
        return "Node({}, {})".format(self.name, self.tags)

    def get_Json_object(self) -> dict:
        return {
            "name": self.name,
            "id": self.id,
            "parent_id": self.parent_id,
            "tag": self.tags,
            "isOpen": self.isOpen,
            "isHighlighted": self.isHighlighted,
            "children": []
        }

    def get_joined_tags(self) -> str:
        if len(self.tags) == 0:
            return ""
        return ", ".join(self.tags)

class Tree:
    def __init__(self, topic: str="root", filename: str=None, KGOutput: str="../../output", stateDirectory: str="../../output/"):

        self.tag_filters = []
        self.number_of_topics = 0
        self.nodes = {}
        self.kg = KnowledgeBase(KGOutput)
        self.stateDirectory = stateDirectory
        self.state = StateStack(self.stateDirectory)

        if filename:
            self.read_csv(filename)
        elif topic:
            node = Node(name=topic, 
                        parent_id=None)
            self.add_node(node)

    def reset_state(self):
        self.state = StateStack(self.stateDirectory)

    def add_node(self, node: Node, addAfter: str=None) -> bool:
        if self.number_of_topics == 0:

            self.number_of_topics += 1

            # Set the root node to be open and highlighted with no parent and tags
            print("Setting root node: ", node.name)
            node.parent_id = None
            node.isOpen = False
            node.isHighlighted = True
            node.tags = []

            self.nodes[node.id] = node
            self.root = node

            return True

        while node.id in self.nodes:
            node.generate_new_id()
        
        if node.parent_id in self.nodes:
            self.nodes[node.id] = node

            if addAfter is None:
                self.nodes[node.parent_id].children.append(node.id)
            else:
                self.nodes[node.parent_id].children.insert(
                    self.nodes[node.parent_id].children.index(addAfter)+1, node.id)

            return True
        else:
            return False

    def print_tree(self) -> None:
        self.print_tree_helper(self.root, 0)
    
    def print_tree_helper(self, node: Node, depth: int) -> None:
        print("\t"*depth, node.name)
        for child_id in node.children:
            self.print_tree_helper(self.nodes[child_id], depth+1)
    
    def generate_json(self, sorting: bool=False):
        tree = self.generate_tree_helper(self.root, sorting)
        tree["isHighlighted"] = True
        tree["isOpen"] = True
        tree = [tree]
        return tree

    def generate_tree_helper(self, node: Node, sorting: bool=False) -> dict:
        node = node.get_Json_object()

        if len(self.tag_filters) > 0 and len(node["tag"]) > 0:
            if not any(tag in self.tag_filters for tag in node["tag"]):
                return None
            
        children = [self.nodes[child_id] for child_id in self.nodes[node["id"]].children]
        lexigraphically_sorted_children = sorted(children, key=lambda x: x.name)
        # print(lexigraphically_sorted_children, children)
        for child in lexigraphically_sorted_children:
            child_node = self.generate_tree_helper(child, sorting)
            if child_node is not None:
                node["children"].append(child_node)
        
        if sorting:
            node["children"] = sorted(node["children"], key=lambda x: (x["isHighlighted"]))

        return node
    
    def remove_node_with_id(self, node_id: str):
        if node_id in self.nodes:
            parent_id = self.nodes[node_id].parent_id
            children_ids = self.nodes[node_id].children
            self.nodes[parent_id].children.remove(node_id)
            for child_id in children_ids:
                self.remove_node_with_id(child_id)
            del self.nodes[node_id]
    
    def set_open(self, node_id: str, isOpen: bool):
        # To open all nodes in the path to the selected node
        # if isOpen:
        #     path = self.get_path(node_id)
        #     for node_id, _ in path:
        #         self.nodes[node_id].isOpen = isOpen
        # else:
        #     if node_id in self.nodes:
        #         self.nodes[node_id].isOpen = isOpen
        if node_id in self.nodes:
            self.nodes[node_id].isOpen = isOpen
            if isOpen and len(self.nodes[node_id].children) == 0:
                self.refresh_suggestions(node_id)
    
    def set_highlight(self, node_id: str, isHighlighted: bool):
        # print("Node ID: {}({}), isHighlighted: {}({})".format(node_id, type(node_id), isHighlighted, type(isHighlighted)))
        if isHighlighted == True:
            path = self.get_path(node_id)
            # print("Path: ", path)
            for parent_node_id, _ in path:
                self.nodes[parent_node_id].isHighlighted = True
        else:
            if node_id in self.nodes:
                self.nodes[node_id].isHighlighted = False
                for child_id in self.nodes[node_id].children:
                    self.set_highlight(child_id, False)
    
    def get_path(self, node_id: str):
        path = []
        while node_id != self.root.id:
            path.append((node_id, self.nodes[node_id].get_joined_tags()))
            node_id = self.nodes[node_id].parent_id
        path.append((node_id, self.nodes[node_id].get_joined_tags()))
        return path[::-1]

    def remove_non_highlighted_nodes(self, node_id: str):
        if node_id in self.nodes:
            children_ids = self.nodes[node_id].children
            for child_id in children_ids:
                if not self.nodes[child_id].isHighlighted:
                    self.remove_node_with_id(child_id)
                
                # To remove all non highlighted nodes below the selected node
                # else:
                #     self.remove_non_highlighted_nodes(child_id)

    def refresh_suggestions(self, node_id: str):
        if node_id in self.nodes:

            # Get all siblings of the selected node
            existing_children = []
            for child_id in self.nodes[node_id].children:
                existing_children.append({
                    "topic": self.nodes[child_id].name,
                    "relation": self.nodes[child_id].tags[0],
                    "is_highlighted": self.nodes[child_id].isHighlighted
                })
            
            path = self.get_path(node_id)
            path = [{"topic": self.nodes[parent_node_id].name, "relation": relation} for parent_node_id, relation in path]
            
            print("Refresh suggestion path: ", path)
            print("Refresh suggestion existing_children: ", existing_children)
            
            self.remove_non_highlighted_nodes(node_id)
            
            suggestions = self.kg.expand_node(topic=self.nodes[node_id].name.lower(), path=path, existing_children=existing_children)

            for dic in suggestions:
                (suggestion, relation) = dic["to"], dic["relation"]
                new_node = Node(name=suggestion, parent_id=node_id, tags=[relation])
                if not self.add_node(new_node):
                    print("Unable to add node: ", new_node)

    def add_relation_based_suggestions_sibling(self, node_id: str, relation: str):
        if node_id in self.nodes:
            # Get all siblings of the selected node
            existing_siblings = []
            parent_id = self.nodes[node_id].parent_id
            for sibling_id in self.nodes[parent_id].children:
                existing_siblings.append({
                    "topic": self.nodes[sibling_id].name,
                    "relation": self.nodes[sibling_id].tags[0],
                    "is_highlighted": self.nodes[sibling_id].isHighlighted
                })
            
            path = self.get_path(node_id)
            path = [{"topic": self.nodes[parent_node_id].name, "relation": relation} for parent_node_id, relation in path]

            suggestions = self.kg.suggest_siblings(topic=self.nodes[node_id].name.lower(), relation=relation, path=path, existing_siblings=existing_siblings)

            for dic in suggestions:
                (suggestion, suggested_relation) = dic["to"], dic["relation"]
                new_node = Node(name=suggestion, parent_id=parent_id, tags=[suggested_relation])
                if not self.add_node(new_node, addAfter=node_id):
                    print("Unable to add node: ", new_node)

        
    def rename_node(self, node_id: str, new_name: str):
        if node_id in self.nodes:
            self.nodes[node_id].name = new_name
    
    def add_tag_to_node(self, node_id: str, tag: str):
        if node_id in self.nodes:
            if tag not in self.nodes[node_id].tags:
                self.nodes[node_id].tags.append(tag)
    
    def remove_tag_from_node(self, node_id: str, tag: str):
        if node_id in self.nodes:
            if tag in self.nodes[node_id].tags:
                self.nodes[node_id].tags.remove(tag)

    def set_node_tag(self, node_id: str, tag: str):
        tag = tag.replace("\n", "")
        if node_id in self.nodes:
            self.nodes[node_id].tags = [tag.upper()] if tag != "" else ["RELATEDTO"]

    def add_tag_to_filter(self, tag: str):
        if tag not in self.tag_filters:
            self.tag_filters.append(tag)
    
    def remove_tag_from_filter(self, tag: str):
        if tag in self.tag_filters:
            self.tag_filters.remove(tag)
    
    def set_tag_filter(self, tags: list):
        self.tag_filters = tags

    def get_node_path(self, node_id: str):

        if node_id not in self.nodes:
            return self.root.name + "/"

        path = self.get_path(node_id)

        cwd = self.root.name
        for (node_id, tags) in path[1:]:
            cwd = cwd + "/ ({}) {}".format(tags, self.nodes[node_id].name)

        return cwd

    def remove_all_tags_from_filter(self):
        self.tag_filters = []

    def remove_same_relation_sibling(self, node_id: str, tag: str):
        if node_id in self.nodes:
            parent_id = self.nodes[node_id].parent_id
            # print("\nAll Nodes: {}\n".format(self.nodes))
            # print("Parent: {}, Children: {}".format(self.nodes[parent_id].name, self.nodes[parent_id].children))
            nodes_to_remove = []
            for child_id in self.nodes[parent_id].children:
                print(self.nodes[child_id])
                if tag in self.nodes[child_id].tags and not self.nodes[child_id].isHighlighted:
                    # print("     Removing node: ", self.nodes[child_id])
                    nodes_to_remove.append(child_id)
            for node_id in nodes_to_remove:
                self.remove_node_with_id(node_id)

    def read_csv(self, filename: str):
        try:
            with open(filename, 'r') as f:
                reader = f.readlines()
                for row in reader:
                    row = row.split(',')
                    id = row[0]
                    name = row[1]
                    parent_id = row[2]
                    isOpen = row[3]
                    isHighlighted = row[4]
                    tags = row[5:]
                    print("id: {}, name: {}, parent_id: {}, isOpen: {}, isHighlighted: {}, tags: {}".format(id, name, parent_id, isOpen, isHighlighted, tags))
                    node = Node(name, parent_id, id, tags, isOpen, isHighlighted)
                    if not self.add_node(node):
                        raise Exception("could not add node: {}".format(node))
            return True
        except Exception as e:
            raise Exception("[Unable to read file: {}] Error: {}".format(filename, e))
            return False

    def write_csv(self, filename: str, updateState: bool = True):
        if updateState:
            self.state.addState(filename)
        file = open(filename, 'w')
        stack_id = [self.root.id]
        while len(stack_id) > 0:
            node_id = stack_id.pop()
            file.write("{},{},{},{},{},{}\n".format(self.nodes[node_id].id,
                                                    self.nodes[node_id].name,   
                                                    self.nodes[node_id].parent_id,
                                                    self.nodes[node_id].isOpen,
                                                    self.nodes[node_id].isHighlighted,
                                                    ",".join(self.nodes[node_id].tags)))
            stack_id.extend(self.nodes[node_id].children)
        file.close()
    
    def load_last_state(self, filename: str):
        (path, fname) = self.state.getLatestState()
        if fname == None:
            return
        self.number_of_topics = 0
        self.nodes = {}
        self.read_csv(path + fname)
        self.write_csv(filename, updateState=False)
        self.state.deleteLatestState()
    
    def is_back_available(self):
        return len(self.state.stack) > 0
    