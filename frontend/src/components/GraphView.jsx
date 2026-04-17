import { useEffect, useRef } from "react";
import * as d3 from "d3";

export default function GraphView() {
  const ref = useRef();

  useEffect(() => {
    const svg = d3.select(ref.current);
    svg.selectAll("*").remove();

    const data = {
      nodes: [
        { id: "user_1" },
        { id: "user_2" },
        { id: "device_mobile" }
      ],
      links: [
        { source: "user_1", target: "device_mobile" },
        { source: "user_2", target: "device_mobile" }
      ]
    };

    const width = 500;
    const height = 300;

    const simulation = d3.forceSimulation(data.nodes)
      .force("link", d3.forceLink(data.links).id(d => d.id))
      .force("charge", d3.forceManyBody().strength(-100))
      .force("center", d3.forceCenter(width / 2, height / 2));

    const link = svg.append("g")
      .selectAll("line")
      .data(data.links)
      .enter()
      .append("line")
      .attr("stroke", "#999");

    const node = svg.append("g")
      .selectAll("circle")
      .data(data.nodes)
      .enter()
      .append("circle")
      .attr("r", 8)
      .attr("fill", "#16a34a");

    simulation.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y);
    });

  }, []);

  return <svg ref={ref} width={700} height={350}></svg>;
}