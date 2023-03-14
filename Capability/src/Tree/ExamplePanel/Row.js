import React, { useState, useEffect, useRef } from "react";
import { FaBan } from "react-icons/fa";
import { FaLongArrowAltRight } from "react-icons/fa";
import { TiTick } from "react-icons/ti";
import { ImCross } from "react-icons/im";


const ExamplePanelOff = () => {
    return (
        <div>
            <FaBan style={{fontSize: "20px", opacity: "1", color: "rgb(197, 143, 59)", fontWeight: "bold"}}/>
        </div>
    );
}

const ExamplePanelPass = () => {
    return (
        <div>
            <div style={{margin: "0px", backgroundColor: "rgb(230, 238, 230)", padding: "2px"}}>
                <TiTick style={{fontSize: "25px", opacity: "1", color: "rgb(61, 125, 68)"}}/>
            </div>
        </div>
    );
}

const ExamplePanelFail = () => {
    return (
        <div>
            <ImCross style={{fontSize: "12px", opacity: "1", color: "rgb(190, 53, 53"}}/>
        </div>
    );
}

const Row = ({exampleData, setSelectedRow, selectedRow}) => {

    const [example, setExample] = useState(null)
    const [offTopic, setOffTopic] = useState(false)
    const [pass, setPass] = useState(true)
    const [fail, setFail] = useState(false)

    useEffect(() => {
        if (example) {
            setExample(exampleData)
            setPass(exampleData.exampleTrue === exampleData.examplePredicted ? true : false)
            setFail(exampleData.exampleTrue !== exampleData.examplePredicted ? true : false)
            console.log("example: ", example)
        }
    });

    const handleRowSelect = () => {
        setSelectedRow(exampleData.id)
    }

    const commitOffTopic = () => {
        setOffTopic(true)
        setPass(false)
        setFail(false)
    };

    const commitPass = () => {
        setOffTopic(false)
        setPass(true)
        setFail(false)
    };

    const commitFail = () => {
        setOffTopic(false)
        setPass(false)
        setFail(true)
    };

    return (
            <tr onClick={() => handleRowSelect()} 
                style={selectedRow === exampleData.id ?
                    {backgroundColor: "rgb(247, 247, 247)"} :
                    {backgroundColor: "rgb(255, 255, 255)"}
            }>
            {/* <tr> */}
            <td>{exampleData.exampleText}</td>
            <td><FaLongArrowAltRight style={{fontSize: "30px", color: "rgb(144, 144, 144)"}}/></td>
            <td>{exampleData.exampleTrue}</td>
            {/* <td></td> */}
            {/* <td></td> */}
            <td onClick={commitOffTopic}>
                {
                    offTopic ?
                        <ExamplePanelOff /> :
                        <FaBan style={{fontSize: "20px", opacity: "0.2"}}/>
                }
            </td>
            <td onClick={commitPass}>
                {
                    pass ?
                        <ExamplePanelPass /> :
                        <TiTick style={{fontSize: "25px", opacity: "0.2"}}/>
                }
            </td>
            <td onClick={commitFail}>
                {
                    fail ?
                        <ExamplePanelFail /> :
                        <ImCross style={{fontSize: "12px", opacity: "0.2"}}/>
                }
            </td>
            </tr>
    );
}

export { Row };