
const config = require("./webpack.config.js");
// webpack.config.js 导出的是函数，需要调用
// 实际 nx 项目的 webpack 配置是通过函数传入的

// 换个方式：直接读取并分析 webpack.config.js 的结构
const fs = require("fs");
const content = fs.readFileSync("./webpack.config.js", "utf-8");

// 找 oneOf 规则
const oneOfIdx = content.indexOf("rule.oneOf");
console.log("oneOf 在位置:", oneOfIdx);
console.log("附近代码:");
console.log(content.substring(oneOfIdx - 200, oneOfIdx + 800));
