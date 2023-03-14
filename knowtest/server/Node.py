from typing import Union
import uuid
import os
import json
from collections import defaultdict

class Example:
    def __init__(self, id: str):
        if id is None:
            self.id = str(uuid.uuid4())
        else:
            self.id = id

        self.exampleText = ""
        self.exampleTrue = ""
        self.examplePredicted = ""
        self.isSuggested = False

    def generate_new_id(self) -> None:
        self.id = str(uuid.uuid4())

    def __JSON__(self) -> dict:
        return {
            "id": self.id,
            "exampleText": self.exampleText,
            "exampleTrue": self.exampleTrue,  #Correct -> label
            "examplePredicted": self.examplePredicted,
            "isSuggested": self.isSuggested
        }

class Node:
    def __init__(self, name: str, parent_id: str, node_id: Union[str, None]=None, tags=[], isOpen: bool=False, isHighlighted: bool=False, examples=[]):
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
        self.natural_language_path = None

        self.examples = defaultdict(Example)
        self.suggested_examples = defaultdict(Example)
        self.add_examples(examples)

    def load_examples(self) -> None:

        # Check if self.nodePath exists and if it does, load the examples
        if os.path.exists(self.nodePath):
            with open(self.nodePath, "r") as f:
                data = json.load(f)
                self.examples = set([Example(example["id"]) for example in data["examples"]])
                self.suggested_examples = set([Example(example["id"]) for example in data["suggested_examples"]])

    
    def process_node(self) -> None:
        # self.name = self.name.capitalize()
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
        self.nodeName = "{}.json".format(self.id)
        self.nodePath = "{}/{}".format(self.nodeDirectory, self.nodeName)

    def __repr__(self) -> str:
        return "Node({}, {})".format(self.name, self.tags)
    
    def add_examples(self, examples: list) -> None:
        for example in examples:
            temp_example = Example(example["id"])
            temp_example.exampleText = example["exampleText"]
            temp_example.exampleTrue = example["exampleTrue"]
            temp_example.examplePredicted = example["examplePredicted"]
            temp_example.isSuggested = example["isSuggested"]

            if example["isSuggested"] == False:
                while temp_example.id in self.examples:
                    temp_example.generate_new_id()
                self.examples[temp_example.id] = temp_example
            else:
                while temp_example.id in self.suggested_examples:
                    temp_example.generate_new_id()
                self.suggested_examples[temp_example.id] = temp_example
    
    def add_example(self, example: Example) -> None:
        if example.isSuggested == False:
            while example.id in self.examples:
                example.generate_new_id()
            self.examples[example.id] = example
        else:
            while example.id in self.suggested_examples:
                example.generate_new_id()
            self.suggested_examples[example.id] = example

    def remove_example(self, example_id: str) -> None:
        if example_id in self.examples:
            del self.examples[example_id]
        elif example_id in self.suggested_examples:
            del self.suggested_examples[example_id]

    def get_Json_object(self) -> dict:

        examples = []
        examples.extend([example.__JSON__() for example in self.examples.values()])
        examples.extend([example.__JSON__() for example in self.suggested_examples.values()])

        return {
            "name": self.name,
            "id": self.id,
            "parent_id": self.parent_id,
            "tag": self.tags,
            "isOpen": self.isOpen,
            "isHighlighted": self.isHighlighted,
            "naturalLanguagePath": self.natural_language_path,
            "children": [],
            "examples": examples
        }

    def get_joined_tags(self) -> str:
        if len(self.tags) == 0:
            return ""
        return ", ".join(self.tags)


