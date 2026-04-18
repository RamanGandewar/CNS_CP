import { useEffect, useRef } from "react";
import * as d3 from "d3";

export default function GraphView({ data }) {
  const ref = useRef(null);

  useEffect(() => {
    if (!data?.nodes?.length) {
      return;
    }

    const svg = d3.select(ref.current);
    svg.selectAll("*").remove();

    const width = 720;
    const height = 360;
    const nodes = data.nodes.map((node) => ({ ...node }));
    const links = data.links.map((link) => ({ ...link }));

    const simulation = d3
      .forceSimulation(nodes)
      .force("link", d3.forceLink(links).id((d) => d.id).distance(120))
      .force("charge", d3.forceManyBody().strength(-280))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(30));

    const link = svg
      .append("g")
      .attr("stroke-opacity", 0.6)
      .selectAll("line")
      .data(links)
      .enter()
      .append("line")
      .attr("stroke", (d) => (d.source.fraud || d.target.fraud ? "#d94f3b" : "#c0c8d4"))
      .attr("stroke-width", (d) => (d.source.fraud || d.target.fraud ? 2 : 1.4))
      .attr("stroke-dasharray", (d) => (d.source.fraud || d.target.fraud ? "5 4" : "0"));

    const node = svg
      .append("g")
      .selectAll("g")
      .data(nodes)
      .enter()
      .append("g");

    node
      .append("circle")
      .attr("r", (d) => (d.type === "user" ? 18 : 14))
      .attr("fill", (d) => (d.fraud ? "#fce8e5" : d.type === "user" ? "#dbeafe" : "#ede9fe"))
      .attr("stroke", (d) => (d.fraud ? "#d94f3b" : "#8ca0b3"))
      .attr("stroke-width", (d) => (d.fraud ? 2.4 : 1.5));

    node
      .append("text")
      .attr("text-anchor", "middle")
      .attr("dy", 4)
      .attr("class", "graph-node-label")
      .text((d) => (d.type === "user" ? "U" : "D"));

    node
      .append("text")
      .attr("text-anchor", "middle")
      .attr("dy", 34)
      .attr("class", "graph-node-name")
      .text((d) => d.label);

    simulation.on("tick", () => {
      link
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y);

      node.attr("transform", (d) => `translate(${d.x},${d.y})`);
    });

    return () => simulation.stop();
  }, [data]);

  return <svg ref={ref} viewBox="0 0 720 360" className="graph-svg" />;
}
