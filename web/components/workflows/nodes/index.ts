import AgentNode from "./agent-node";
import ParallelNode from "./parallel-node";
import ConditionalNode from "./conditional-node";
import LoopNode from "./loop-node";

export const nodeTypes = {
  agentNode: AgentNode,
  parallelNode: ParallelNode,
  conditionalNode: ConditionalNode,
  loopNode: LoopNode,
};

export { AgentNode, ParallelNode, ConditionalNode, LoopNode };
