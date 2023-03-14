from typing import Union
import uuid
import os
import json
import sys
from ..knowledge.knbase import KnowledgeBase
from ..knowledge.relations import to_nl_tags
from ..knowledge.knbase import run_kb_contruction
from .StateStack import StateStack
from .Node import Node
from ..knowledge.relations import path_to_nl_description
from .Node import Example

class Tree:
    def __init__(self, topic: str="root", filename: str=None, KGOutput: str="../output", stateDirectory: str="../output", firstLoad: int=1):

        self.tag_filters = []
        self.number_of_topics = 0
        self.nodes = {}

        # if not KGOutput + "_".join(topic.split(" ")) in os.listdir(KGOutput):
        print(os.path.join(KGOutput, "_".join(topic.split(" "))))
        if not os.path.exists(os.path.join(KGOutput, "_".join(topic.split(" ")))):
            print("Running Knowledge Base Construction")
            run_kb_contruction(topic, 3, KGOutput)

        self.kg = KnowledgeBase(KGOutput, "_".join(topic.split(" ")))
        self.stateDirectory = stateDirectory + "/"
        self.state = StateStack(self.stateDirectory)
        self.only_highlighted = False
        self.firstLoad = firstLoad

        if filename:
            self.read_json(filename)
        elif topic:
            node = Node(name=topic, 
                        parent_id=None)
            self.add_node(node)
            data = self.kg.initialize_tree(topic=topic)
            self.add_initial_data(data)

    def set_only_highlighted(self, only_highlighted: bool):
        print("Setting only highlighted to: ", only_highlighted)
        self.only_highlighted = only_highlighted

    def reset_state(self):
        self.state = StateStack(self.stateDirectory)

    def add_node(self, node: Node, addAfter: str=None) -> bool:
        if self.number_of_topics == 0:
            self.number_of_topics += 1

            # Set the root node to be open and highlighted with no parent and tags
            print("Setting root node: ", node.name)
            node.parent_id = None
            # node.isOpen = False
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
                # position_to_add = self.nodes[node.parent_id].children.index(addAfter)
                self.nodes[node.parent_id].children.insert(
                    self.nodes[node.parent_id].children.index(addAfter)+1, node.id)
                
            node.natural_language_path = self.get_nl_path(node.id)

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
        tree = [tree]

        if self.firstLoad > 0:
            self.firstLoad -= 1
            for child in tree[0]["children"]:
                child["isOpen"] = True
                for grandchild in child["children"]:
                    grandchild["isOpen"] = True

        return tree

    def generate_tree_helper(self, node: Node, sorting: bool=False) -> dict:

        # node.natural_language_path = self.get_natural_language_path(node.id)
        node = node.get_Json_object()
        if len(self.tag_filters) > 0 and len(node["tag"]) > 0:
            if not any(tag in self.tag_filters for tag in node["tag"]):
                return None
            
        children = [self.nodes[child_id] for child_id in self.nodes[node["id"]].children]
        
        if sorting:
            children = sorted(children, key=lambda x: x.name)
        
        for child in children:
            if self.only_highlighted and not child.isHighlighted:
                continue
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
    
    def get_nl_path(self, node_id: str):
        path = self.get_path(node_id)
        path = [{"topic": self.nodes[parent_node_id].name, "relation": relation} for parent_node_id, relation in path]
        return path_to_nl_description(path)

    # def get_natural_language_relation(self, parent: str, child: str, child_tag: str):
    #     if child_tag.lower() == "atlocation":
    #         return "At location {}".format(child)
    #     elif child_tag.lower() == "relatedto":
    #         return "{} is related to {}".format(child, parent)
    #     elif child_tag.lower() == "typesof":
    #         return "{} is a type of {}".format(child, parent)
    #     elif child_tag.lower() == "partof":
    #         return "{} is a part of {}".format(child, parent)
    #     elif child_tag.lower() == "hasproperty":
    #         return "{} has property {}".format(parent, child)
    #     elif child_tag.lower() == "usedfor":
    #         return "{} is used for {}".format(parent, child)
    #     elif child_tag.lower() == "causes":
    #         return "{} causes {}".format(parent, child)
    #     elif child_tag.lower() == "motivatedby":
    #         return "{} is motivated by {}".format(parent, child)
    #     elif child_tag.lower() == "obstructedby":
    #         return "{} is obstructed by {}".format(parent, child)
    #     elif child_tag.lower() == "mannerof":
    #         return "{} is a manner of {}".format(child, parent)
    #     elif child_tag.lower() == "locatednear":
    #         return "{} is located near {}".format(parent, child)
    #     elif child_tag.lower() == "hasagent":
    #         return "{} has agent {}".format(parent, child)
    #     elif child_tag.lower() == "haspatient":
    #         return "{} has patient {}".format(parent, child)
    #     else:
    #         return "{} is related to {}".format(child, parent)

    # def get_natural_language_path(self, node_id: str):
    #     path = self.get_path(node_id)
    #     path = path[::-1]
    #     natural_language_path = ""
    #     for child, parent in zip(path, path[1:]):
    #         child_id, child_tag = child
    #         parent_id, parent_tag = parent
    #         # print(self.nodes[parent_id].name, self.nodes[child_id].name, child_tag)
    #         natural_language_path += self.get_natural_language_relation(self.nodes[parent_id].name, self.nodes[child_id].name, child_tag)
    #         natural_language_path += ". "
        
    #     return natural_language_path

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
            
            # self.remove_non_highlighted_nodes(node_id) # DISABLED
            
            suggestions = self.kg.expand_node(topic=self.nodes[node_id].name.lower(), path=path, existing_children=existing_children)

            for dic in suggestions:
                (suggestion, relation) = dic["to"], to_nl_tags(dic["relation"])
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
                (suggestion, suggested_relation) = dic["to"], to_nl_tags(dic["relation"])
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
    
    def add_example(self, node_id: str, exampleText: str, exampleTrue: str, examplePredicted, isSuggested: bool):
        if node_id in self.nodes:
            example = Example(id=None)
            example.exampleText = exampleText
            example.exampleTrue = exampleTrue
            example.examplePredicted = examplePredicted
            example.isSuggested = isSuggested
            self.nodes[node_id].add_example(example)
    
    def remove_example(self, node_id: str, exampleID: str):
        if node_id in self.nodes:
            self.nodes[node_id].remove_example(exampleID)

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
                
    def add_initial_data(self, data: dict):
        for node_data in data:
            for node in self.nodes.values():
                if node.name == node_data["parent"]:
                    parent_id = node.id
                    temp_node = Node(name=node_data['topic'], 
                                     parent_id=parent_id, 
                                     tags=[node_data['relation']])
                    self.add_node(temp_node)
                    break

                        

    def read_json(self, filename: str):
        try:
            with open(filename, 'r') as f:
                master_JSON = json.load(f)
                for node in master_JSON:
                    node = Node(name=node["name"], 
                                parent_id=node["parent_id"], 
                                node_id=node["id"], 
                                tags=node["tag"], 
                                isOpen=node["isOpen"], 
                                isHighlighted=node["isHighlighted"],
                                examples=node["examples"])

                    if not self.add_node(node):
                        raise Exception("could not add node: {}".format(node))
        except Exception as e:
            raise Exception("[Unable to read file: {}] Error: {}".format(filename, e))
            return False
        

    def write_json(self, filename: str, updateState: bool = True):
        if updateState:
            self.state.addState(filename)
        stack_id = [self.root.id]
        master_JSON = []
        while len(stack_id) > 0:
            node_id = stack_id.pop()
            master_JSON.append(self.nodes[node_id].get_Json_object())
            stack_id.extend(self.nodes[node_id].children[::-1])
        with open(filename, 'w') as f:
            json.dump(master_JSON, f, indent=4)
    
    def load_last_state(self, filename: str):
        (path, fname) = self.state.getLatestState()
        if fname == None:
            return
        self.number_of_topics = 0
        self.nodes = {}
        self.read_json(path + fname)
        self.write_json(filename, updateState=False)
        self.state.deleteLatestState()
    
    def is_back_available(self):
        return len(self.state.stack) > 0
    