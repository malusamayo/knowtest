from typing import Union
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import asyncio
import uvicorn
import threading
from fastapi.responses import FileResponse
import os
import sys
from .Tree import Tree, Node
import logging

# checkif ./Data folder exists and create it if not
# if not os.path.exists("Data"):
#     os.mkdir("Data")

# filename = "../../output/"
# t = Tree(filename=filename, topic="hate speech")

class CapabilityApp:
    def __init__(self, topic: str, filename: str="../output/", serverHost: str="0.0.0.0", serverPort: int=3001):
        self.filename = filename
        self.topic = topic
        self.topic = "_".join(topic.split(" "))
        self.filepath = self.filename + self.topic + ".json"
        self.change_topic(topic)

        self.serverHost = serverHost
        self.serverPort = serverPort
        self.serverRunning = False

        self.app = FastAPI()

        @self.app.get("/")
        def get_tree():
            # t.reset_state()
            return self.t.generate_json()

        @self.app.get("/addNode/parentID={parent_id}&nodeName={name}&nodeTag={tag}")
        def add_node(parent_id: str, name: str, tag: str):
            node = Node(name=name, parent_id=parent_id, tags=[tag])
            self.t.add_node(node)
            self.t.set_highlight(node.id, True)
            self.t.write_json(self.filepath)
            return self.t.generate_json()

        @self.app.get("/editFolderName/nodeId={node_id}&newName={new_name}")
        def edit_folder_name(node_id: str, new_name: str):
            self.t.rename_node(node_id, new_name)
            self.t.write_json(self.filepath)
            return self.t.generate_json()

        @self.app.get("/deleteNode/nodeId={node_id}")
        def delete_node(node_id: str):
            self.t.remove_node_with_id(node_id)
            self.t.write_json(self.filepath)
            return self.t.generate_json()

        @self.app.get("/setOpen/nodeId={node_id}&isOpen={bool}")
        def set_open(node_id: str, bool: bool):
            self.t.set_open(node_id, bool)
            self.t.write_json(self.filepath)
            return self.t.generate_json()

        @self.app.get("/setHighlighted/nodeId={node_id}&isHighlighted={bool}")
        def set_highlight(node_id: str, bool: bool):
            self.t.set_highlight(node_id, bool)
            self.t.write_json(self.filepath)
            return self.t.generate_json()

        @self.app.get("/getNodePath/nodeId={node_id}")
        def get_node_path(node_id: str):
            print("Getting node path for: ", node_id)
            return self.t.get_node_path(node_id)

        @self.app.get("/setNodeTag/nodeId={node_id}&tag={tag}")
        def set_node_tag(node_id: str, tag: str):
            print("Setting node tag ({}) for: {}".format(tag, node_id))
            self.t.set_node_tag(node_id, tag)
            self.t.write_json(self.filepath)
            return self.t.generate_json()

        @self.app.get("/setTagFilter/tags={tags}")
        def set_tag_filter(tags: str):
            tags = tags.split(",")
            print("Setting tag filter: ", tags)
            self.t.set_tag_filter(tags)
            return self.t.generate_json()

        @self.app.get("/resetTagFilter")
        def reset_tag_filter():
            print("Resetting tag filter")
            self.t.set_tag_filter([])
            return self.t.generate_json()

        @self.app.get("/getSuggestions/nodeId={node_id}")
        def get_suggestion(node_id: str):
            print("Getting suggestion for: ", node_id)
            self.t.set_open(node_id, True)
            self.t.refresh_suggestions(node_id)
            self.t.write_json(self.filepath)
            return self.t.generate_json()

        @self.app.get("/removeSimilarRelationSiblings/nodeId={node_id}&tag={relation}")
        def remove_similar_relation_siblings(node_id: str, relation: str):
            # print("Removing similar relation children for {} with tag {}".format(t.nodes[t.nodes[node_id].parent_id], relation))
            self.t.remove_same_relation_sibling(node_id, relation)
            self.t.write_json(self.filepath)
            return self.t.generate_json()

        @self.app.get("/addSimilarRelationSiblings/nodeId={node_id}&tag={relation}")
        def add_similar_relation_siblings(node_id: str, relation: str):
            print("Adding siblings with relation: ", relation)
            self.t.add_relation_based_suggestions_sibling(node_id, relation)
            self.t.write_json(self.filepath)
            return self.t.generate_json()

        @self.app.get("/previousState")
        def previous_state():
            print("Going to previous state")
            self.t.load_last_state(self.filepath)
            return self.t.generate_json()

        @self.app.get("/isBackAvailable")
        def is_back_available():
            return self.t.is_back_available()

        @self.app.get("/resetState")
        def reset_state():
            print("Resetting state")
            self.t.reset_state()

        @self.app.get("/getTopics/isHighlighted={highlighted}")
        def get_topics(highlighted: bool):
            self.t.set_only_highlighted(highlighted)
            return self.t.generate_json()

        @self.app.get("/toggleIsHighlightedSelection")
        def toggle_is_highlighted_selection():
            return self.t.only_highlighted
        
        @self.app.get("/addExample/nodeId={node_id}&exampleText={example_text}&exampleTrue={example_true}&isSuggested={is_suggested}")
        def add_example(node_id: str, example_text: str, example_true: str, is_suggested: bool):
            # TODO: Predict
            example_predicted = "True"

            self.t.add_example(node_id, example_text, example_true, example_predicted, is_suggested)
            self.t.write_json(self.filepath)
            return "Done"
        
        @self.app.get("/removeExample/nodeID={node_id}&exampleID={example_id}")
        def remove_example(node_id: str, example_id: str):
            self.t.remove_example(node_id, example_id)
            self.t.write_json(self.filepath)
            return self.t.generate_json()

        
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def change_topic(self, topic: str):
        self.topic = "_".join(topic.split(" "))
        self.filepath = self.filename + self.topic + ".json"

        if not os.path.exists(self.filepath):
            self.t = Tree(topic=topic)
            self.t.write_json(self.filepath)
        else:
            self.t = Tree(topic=topic, filename=self.filepath)

    def initializeServer(self):

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        def run(loop):
            asyncio.set_event_loop(loop)
            self.running = True
            while self.running:
                uvicorn.run(self.app, host=self.serverHost, port=self.serverPort, log_level="error")
        
        print("Starting server on port: ", self.serverPort)
        thread = threading.Thread(target=run, args=(loop,))
        thread.start()
    
    def stopServer(self):
        print("Stopping server")
        self.running = False

        
if __name__ == "__main__":
    server = CapabilityApp(topic="hate speech")
    uvicorn.run(server.app, host="0.0.0.0", port=3001, log_level="info")
        


# app = FastAPI()

# @app.get("/")
# def get_tree():
#     # t.reset_state()
#     return t.generate_json()

# @app.get("/addNode/parentID={parent_id}&nodeName={name}&nodeTag={tag}")
# def add_node(parent_id: str, name: str, tag: str):
#     node = Node(name=name, parent_id=parent_id, tags=[tag])
#     t.add_node(node)
#     t.set_highlight(node.id, True)
#     t.write_json(filename)
#     return t.generate_json()

# @app.get("/editFolderName/nodeId={node_id}&newName={new_name}")
# def edit_folder_name(node_id: str, new_name: str):
#     t.rename_node(node_id, new_name)
#     t.write_json(filename)
#     return t.generate_json()

# @app.get("/deleteNode/nodeId={node_id}")
# def delete_node(node_id: str):
#     t.remove_node_with_id(node_id)
#     t.write_json(filename)
#     return t.generate_json()

# @app.get("/setOpen/nodeId={node_id}&isOpen={bool}")
# def set_open(node_id: str, bool: bool):
#     t.set_open(node_id, bool)
#     t.write_json(filename)
#     return t.generate_json()

# @app.get("/setHighlighted/nodeId={node_id}&isHighlighted={bool}")
# def set_highlight(node_id: str, bool: bool):
#     t.set_highlight(node_id, bool)
#     t.write_json(filename)
#     return t.generate_json()

# @app.get("/getNodePath/nodeId={node_id}")
# def get_node_path(node_id: str):
#     print("Getting node path for: ", node_id)
#     return t.get_node_path(node_id)

# @app.get("/setNodeTag/nodeId={node_id}&tag={tag}")
# def set_node_tag(node_id: str, tag: str):
#     print("Setting node tag ({}) for: {}".format(tag, node_id))
#     t.set_node_tag(node_id, tag)
#     t.write_json(filename)
#     return t.generate_json()

# @app.get("/selectTopic/topic={topic}")
# def select_topic(topic: str):
#     print("Selecting topic: ", topic)

#     filename = "Data/{}.json".format(topic)
#     if not os.path.exists(filename):
#         t = Tree(topic=topic)
#         t.write_json(filename)
#     else:
#         t = Tree(filename=filename)

#     return t.generate_json()

# @app.get("/setTagFilter/tags={tags}")
# def set_tag_filter(tags: str):
#     tags = tags.split(",")
#     print("Setting tag filter: ", tags)
#     t.set_tag_filter(tags)
#     return t.generate_json()

# @app.get("/resetTagFilter")
# def reset_tag_filter():
#     print("Resetting tag filter")
#     t.set_tag_filter([])
#     return t.generate_json()

# @app.get("/getSuggestions/nodeId={node_id}")
# def get_suggestion(node_id: str):
#     print("Getting suggestion for: ", node_id)
#     t.set_open(node_id, True)
#     t.refresh_suggestions(node_id)
#     t.write_json(filename)
#     return t.generate_json()

# @app.get("/removeSimilarRelationSiblings/nodeId={node_id}&tag={relation}")
# def remove_similar_relation_siblings(node_id: str, relation: str):
#     # print("Removing similar relation children for {} with tag {}".format(t.nodes[t.nodes[node_id].parent_id], relation))
#     t.remove_same_relation_sibling(node_id, relation)
#     t.write_json(filename)
#     return t.generate_json()

# @app.get("/addSimilarRelationSiblings/nodeId={node_id}&tag={relation}")
# def add_similar_relation_siblings(node_id: str, relation: str):
#     print("Adding siblings with relation: ", relation)
#     t.add_relation_based_suggestions_sibling(node_id, relation)
#     t.write_json(filename)
#     return t.generate_json()

# @app.get("/previousState")
# def previous_state():
#     print("Going to previous state")
#     t.load_last_state(filename)
#     return t.generate_json()

# @app.get("/isBackAvailable")
# def is_back_available():
#     return t.is_back_available()

# @app.get("/resetState")
# def reset_state():
#     print("Resetting state")
#     t.reset_state()

# @app.get("/getTopics/isHighlighted={highlighted}")
# def get_topics(highlighted: bool):
#     t.set_only_highlighted(highlighted)
#     return t.generate_json()

# @app.get("/toggleIsHighlightedSelection")
# def toggle_is_highlighted_selection():
#     return t.only_highlighted

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=False,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )