import React, { useState, useEffect, useLayoutEffect } from "react";
import { Tooltip } from 'react-tooltip';
import {
  AiOutlineFolder,
  AiOutlineFolderOpen,
  AiOutlinePlus,
  AiFillEdit,
  AiOutlineMinus,
  AiFillFolder,
  AiFillFolderOpen,
} from "react-icons/ai";

import { MdDeleteForever } from "react-icons/md";
import { FaFolderPlus } from "react-icons/fa";
import { BiRefresh, BiPlusMedical } from "react-icons/bi";
import { BsSearch, BsFillPlusCircleFill } from "react-icons/bs";
import { ImPlus, ImCross } from "react-icons/im";

import {
  ActionsWrapper,
  Collapse,
  StyledName,
  VerticalLine,
  StyledTag,
  StyledAddTopic,
} from "../Tree.style";
import { StyledFolder } from "./TreeFolder.style";

import { useTreeContext } from "../state/TreeContext";
import { PlaceholderInput } from "../TreePlaceholderInput";
import {fetchAPIDATA} from "../../utils";
import { Dropdown } from "../Dropdown/dropdown";
import { AlertDelete } from "./AlertDelete";
import { size } from "lodash";

const StyledRelation = ({node, nodeTag}) => {

  const { dispatch, setIsLoading } = useTreeContext();

  const commitRemoveSimilarRelationSiblings = async (node, nodeTag) => {
    try {
      const newData = await fetchAPIDATA("removeSimilarRelationSiblings/nodeId=" + node.id + "&tag=" + nodeTag);
      dispatch({ type: "SET_DATA", payload: newData });
    } catch (error) {
      console.log(error);
    }
  }

  const commitAddSimilarRelationSiblings = async (node, nodeTag) => {
    try {
      setIsLoading(true);
      const newData = await fetchAPIDATA("addSimilarRelationSiblings/nodeId=" + node.id + "&tag=" + nodeTag);
      dispatch({ type: "SET_DATA", payload: newData });
      setIsLoading(false);
    } catch (error) {
      console.log(error);
    }
  }

  const handleActionPlusClick = (event) => {
    event.stopPropagation();
    console.log("handleActionPlusClick", event)
    commitAddSimilarRelationSiblings(node, nodeTag)
  }

  const handleActionCrossClick = (event) => {
    event.stopPropagation();
    console.log("handleActionCrossClick", event)
    commitRemoveSimilarRelationSiblings(node, nodeTag)
  }

  return (
    <StyledTag>
      <div style={{alignItems:"top"}}>
        {nodeTag}
      </div>
      <div className="actionbutton">
        <ImPlus onClick={handleActionPlusClick} />
        &nbsp;&nbsp;
        <ImCross onClick={handleActionCrossClick} />
      </div>
    </StyledTag>
  )
}

const FolderName = ({ isOpen, name, handleClick, isHighlighted, node, isEditing, type, setNodeHighlighted}) => {

  if (type === "specialAddSuggestion") {
    return (
      <StyledName onClick={handleClick}>
        <BiRefresh /> &nbsp;&nbsp; {name} 
      </StyledName>
    )
  }

  let parentName = node.parentNode.name
  let nodeTag = node.tag[0]

  if (type === "folderCreation") {
    console.log("FolderName", node, type, isEditing, node.tag.length)
    parentName = node.name
    nodeTag = "RELATEDTO"
  }

  const tooltip_style= {
    zIndex: 9999, 
    position: "absolute", 
    backgroundColor: "rgba(54, 54, 54, 1)",
    padding : "5px",
    fontSize: "80%",
  };
  
  // make const anchor_id = "node-info-" + node.id and all spaces in node.id to be replaced by "-"
  const anchor_id = "node-info-" + node.id;

  const handleNodeHighlight = (event) => {
    event.stopPropagation();
    setNodeHighlighted(!isHighlighted)
  }

  return (
    <StyledName onClick={handleClick}>
      {
        isHighlighted ?
          isOpen ? <AiFillFolderOpen onClick={handleNodeHighlight}/> : <AiFillFolder onClick={handleNodeHighlight}/> :
          isOpen ? <AiOutlineFolderOpen onClick={handleNodeHighlight}/> : <AiOutlineFolder onClick={handleNodeHighlight}/>
      }
      {!isEditing ? 
        node.tag.length > 0 ? node.tag.map((tag, index) => <StyledRelation node={node} nodeTag={tag} key={index}/>) : null :
        node.tag.length ? (<Dropdown node={node}/>): null
      }
      &nbsp;&nbsp;
      <div id={anchor_id}>
        {name}
      </div>
      {/* <Tooltip place="top" anchorSelect={"#" + anchor_id} content={node.naturalLanguagePath} style={tooltip_style}/> */}
    </StyledName>
  )
};

// const SpecialAddTopicFolder = ({commitSuggestions}) => {
//   return (
//     <p onClick={commitSuggestions}>... Add Topics</p>
//   );
// }

const Folder = ({ id, name, children, node, root}) => {
  const { dispatch, onNodeClick, setIsLoading } = useTreeContext();
  const [isEditing, setEditing] = useState(false);
  const [isOpen, setIsOpen] = useState(node.isOpen);
  const [childs, setChilds] = useState([]);
  const [isDeleting, setIsDeleting] = useState(false);

  // Setting new const here
  const [tags, setTags] = useState(node.tags);

  const setNodeOpen = async (open) => {
    try {
      if (open) {
        setIsLoading(true);
      }

      const newData = await fetchAPIDATA("setOpen/nodeId=" + node.id + "&isOpen=" + open);
      dispatch({ type: "SET_DATA", payload: newData });
      setIsOpen(open);
      
      if (open) {
        setIsLoading(false);
      }

    } catch (error) {
      console.error(error);
    }
  };

  const setNodeHighlighted = async (highlighted) => {
    try {
      const newData = await fetchAPIDATA("setHighlighted/nodeId=" + node.id + "&isHighlighted=" + highlighted);
      dispatch({ type: "SET_DATA", payload: newData });
      // setHighlighted(highlighted);
    } catch (error) {
      console.error(error);
    }
  };

  useLayoutEffect(() => {
    setIsOpen(node.isOpen);
  }, [node.isOpen]);

  useEffect(() => {
    setTags(node.tags);
  }, [node.tags]);

  useEffect(() => {
    setChilds([children]);
  }, [children]);

  const commitFolderCreation = async (name) => {
    try {
      if (name === "") {
        name = "New Topic";
      }
      console.log("commitFolderCreation");
      const newData = await fetchAPIDATA("addNode/parentID=" + node.id + "&nodeName=" + name + "&nodeTag=RELATEDTO");
      dispatch({ type: "SET_DATA", payload: newData });
      setEditing(false);
    } catch (error) {
      console.error(error);
    }
  };
  const commitDeleteFolder = async () => {
    try {
      const newData = await fetchAPIDATA("deleteNode/nodeId=" + node.id);
      dispatch({ type: "SET_DATA", payload: newData });
      setEditing(false);
    } catch (error) {
      console.error(error);
    }
  };

  const handleDeleteConfirm = () => {
    console.log("Handle Delete Confirm");
    setIsDeleting(true);
  };

  const handleDeleteFolder = () => {
    console.log("Handle Delete Folder")
    if (!node.isHighlighted) {
      commitDeleteFolder();
    } else {
      handleDeleteConfirm();
    }
  };

  const commitFolderEdit = async (name) => {
    try {
      const newData = await fetchAPIDATA("editFolderName/nodeId=" + id + "&newName=" + name);
      dispatch({ type: "SET_DATA", payload: newData });
      setEditing(false);
    } catch (error) {
      console.error(error);
    }
  };

  const commitSuggestions = async () => {
    try {

      setIsLoading(true);
      const newData = await fetchAPIDATA("getSuggestions/nodeId=" + id);
      dispatch({ type: "SET_DATA", payload: newData });
      setEditing(false);
      setIsLoading(false);
    } catch (error) {
      console.error(error);
    }
  };

  const handleCancel = () => {
    setEditing(false);
    setChilds([children]);
  };

  const handleNodeClick = React.useCallback(
    (event) => {
      event.stopPropagation();
      onNodeClick({ node });
    },
    [node]
  );

  const handleFolderCreation = (event) => {
    event.stopPropagation();
    setIsOpen(true);
    console.log("handleFolderCreation");
    setChilds([
      ...childs,
      <PlaceholderInput
        type="folderCreation"
        onSubmit={commitFolderCreation}
        onCancel={handleCancel}
        defaultValue="New Topic"
        node={node}
        isEditing={false}
      />,
    ]);
  };

  const handleFolderRename = () => {
    setNodeOpen(true)
    setEditing(true);
  };

  // handle hover over className="AddFolder"
  useEffect(() => {
    const handleMouseOverForAddFolder = (event) => {
      if (event.target.className === "AddFolder") {
        // Show a box with the text "Add Topic" in it
        console.log("Mouse Over Add Folder");
      }
    };
    document.addEventListener("mouseover", handleMouseOverForAddFolder);
    return () => {
      document.removeEventListener("mouseover", handleMouseOverForAddFolder);
    };
  }, []);

  const tooltip_style= {
    zIndex: 9999, 
    position: "absolute", 
    backgroundColor: "rgba(54, 54, 54, 1)",
    padding : "5px",
    fontSize: "80%",
  };

  return (
    <StyledFolder id={id} onClick={handleNodeClick} className="tree__folder">
        <AlertDelete node={node} onConfirm={commitDeleteFolder} isDeleting={isDeleting} setIsDeleting={setIsDeleting}/>
        <VerticalLine root={false}>
          <ActionsWrapper>
            {/* {root ? (<div style={{marginRight: "15px"}} >></div>) : null} */}
            {/* {node.tag.length ? (<Dropdown node={node}/>): null} */}
            {isEditing ? (
              <PlaceholderInput
                style={{ paddingLeft: 0}}
                isHighlighted={node.isHighlighted}
                defaultValue={name}
                node={node}
                onCancel={handleCancel}
                onSubmit={commitFolderEdit}
                isEditing={true}
              />
            ) : (
              <FolderName
                name={name}
                isOpen={isOpen}
                isHighlighted={node.isHighlighted}
                setNodeHighlighted={setNodeHighlighted}
                node={node}
                handleClick={() => setNodeOpen(!isOpen)}
              />
            )}

            <div className="actions">
              {/* {root ? null : node.isHighlighted ?
                <AiOutlineMinus onClick={() => setNodeHighlighted(false)} id="unhighlight-topic"/> :
                <AiOutlinePlus onClick={() => setNodeHighlighted(true)} id="highlight-topic"/> } */}
              <BsSearch id="example-panel-explore"/>
              {/* <BiRefresh onClick={commitSuggestions} id="refresh-suggestion"/> */}
              <AiFillEdit onClick={handleFolderRename} id="edit-topic"/>
              <FaFolderPlus onClick={handleFolderCreation} id="add-topic"/>
              {root ? null : <MdDeleteForever onClick={handleDeleteFolder} id="delete-topic"/>}
              <Tooltip place="bottom" anchorSelect="#highlight-topic" content="Highlight the Topic" style={tooltip_style}/>
              <Tooltip place="bottom" anchorSelect="#example-panel-explore" content="Explore the Topic" style={tooltip_style}/>
              <Tooltip place="bottom" anchorSelect="#unhighlight-topic" content="Unhighlight the Topic" style={tooltip_style}/>
              <Tooltip place="bottom" anchorSelect="#refresh-suggestion" content="Refresh Suggestions" style={tooltip_style}/>
              <Tooltip place="bottom" anchorSelect="#edit-topic" content="Edit Topic" style={tooltip_style}/>
              <Tooltip place="bottom" anchorSelect="#add-topic" content="Add Topic" style={tooltip_style}/>
              <Tooltip place="bottom" anchorSelect="#delete-topic" content="Delete Topic" style={tooltip_style}/>
            </div>
          </ActionsWrapper>
          {(node.isOpen || isOpen) && (
            <Collapse className="tree__folder--collapsible" isOpen={isOpen}>
            {childs}
            <StyledName onClick={commitSuggestions} 
              style={{
                paddingLeft: "22px",
                fontSize: "100%",
                color: "rgba(167, 20, 168, 1)",
              }}>
              <BsFillPlusCircleFill style={{fontSize: "80%", opacity:"0.8"}}/> &nbsp;&nbsp; 
              <div style={{
                display: "inline-block",
                // padding: "2px"
              }}>Show more topics for "{name}"</div>
            </StyledName>
          </Collapse>
          )}
        </VerticalLine>
    </StyledFolder>
  );
};

export { Folder, FolderName };
