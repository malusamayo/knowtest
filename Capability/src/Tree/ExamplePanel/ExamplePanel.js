import React, { useState, useEffect, useRef } from "react";
import {fetchAPIDATA} from "../../utils";
import { examplePanel } from "./ExamplePanel.css";
import { HiOutlineBan } from "react-icons/hi";
import { FaLongArrowAltRight } from "react-icons/fa";
import { TiTick } from "react-icons/ti";
import { ImCross } from "react-icons/im";
import { Row } from "./Row";

const ExamplePanelOff = () => {
    return (
        <div>
            <HiOutlineBan style={{fontSize: "20px", opacity: "1", color: "rgb(197, 143, 59)"}}/>
        </div>
    )
}

const ExamplePanel = ({node}) => {

    // uddate the node state when the node prop changes
    const [selectedNode, setSelectedNode] = useState(null)
    const [selectedRow, setSelectedRow] = useState(null)

    useEffect(() => {
        if (node) {
            setSelectedNode(node.node)
        }
    }, [node]);

    useEffect(() => {
    }, [selectedRow]);

    // Set example-panel-container top to the bottom of menu_top_tree_toolbar
    useEffect(() => {
        const examplePanelContainer = divRef.current;
        const menuTopTreeToolbar = document.getElementById("menu_top_tree_toolbar");
        const menuTopTreeToolbarBox = menuTopTreeToolbar.getBoundingClientRect();

        examplePanelContainer.style.top = menuTopTreeToolbarBox.bottom + 20 + "px";
    }, []);
        

    const divRef = useRef(null);

    return (
        <div className="example-panel" ref={divRef}>
            <div className="example-panel__content">
                <h4>Example Panel</h4>
                {selectedNode &&
                    <div>
                        <p>Topic: {selectedNode.name}</p>   
                        <table className="example-panel-selected-table">
                            <thead>
                            <tr>
                                <td>Input</td>
                                <td></td>
                                <td>Output</td>
                                <td>Off-topic</td> 
                                <td>Pass</td>
                                <td>Fail</td>
                            </tr>
                            </thead>
                            <tbody>
                            {
                                selectedNode.examples.map((example, index) => {
                                    // console.log("example: ", example)
                                    if (example.isSuggested === false) {
                                        return (
                                            <Row 
                                                exampleData={example}
                                                key={index}
                                                setSelectedRow={setSelectedRow}
                                                selectedRow={selectedRow}
                                            />

                                        )
                                    }
                                })
                            }
                            </tbody>
                        </table>
                        <br/> <br/>
                        <table className="example-panel-selected-table">
                            <tbody>
                            {
                                selectedNode.examples.map((example, index) => {
                                    // console.log("example: ", example)
                                    if (example.isSuggested === false) {
                                        return (
                                            <Row 
                                                exampleData={example}
                                                key={index}
                                                setSelectedRow={setSelectedRow}
                                                selectedRow={selectedRow}
                                            />

                                        )
                                    }
                                })
                            }
                            </tbody>
                        </table>
                    </div>
                }
            </div>
        </div>
    );
}

export { ExamplePanel };