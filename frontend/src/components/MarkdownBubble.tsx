import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import rehypeSanitize, { defaultSchema } from "rehype-sanitize";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";

// (optional) allow some extra tags/attrs beyond default sanitize
const schema = {
  ...defaultSchema,
  attributes: {
    ...defaultSchema.attributes,
    code: [...(defaultSchema.attributes?.code || []), ["className"]],
    span: [...(defaultSchema.attributes?.span || []), ["className"]],
    kbd: [["className"]],
  },
};

type Props = { text: string; className?: string };

export default function MarkdownBubble({ text, className }: Props) {
  return (
    <div className={className}>
      <ReactMarkdown
        // GitHub tables, lists, task-lists, etc.
        remarkPlugins={[remarkGfm, remarkMath]}
        // allow limited raw HTML but sanitize it
        rehypePlugins={[
          rehypeRaw,
          [rehypeSanitize, schema],
          rehypeKatex, // remove if you don't need LaTeX
        ]}
        // map elements for styling & code highlight
        components={{
          code({ inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || "");
            return !inline && match ? (
              <SyntaxHighlighter language={match[1]} PreTag="div" {...props}>
                {String(children).replace(/\n$/, "")}
              </SyntaxHighlighter>
            ) : (
              <code className="px-1 py-0.5 rounded bg-gray-100" {...props}>
                {children}
              </code>
            );
          },
          a({ children, ...props }) {
            return (
              <a
                {...props}
                target="_blank"
                rel="noopener noreferrer"
                className="underline decoration-dotted hover:decoration-solid"
              >
                {children}
              </a>
            );
          },
          ul({ children }) {
            return <ul className="list-disc pl-5 my-2">{children}</ul>;
          },
          ol({ children }) {
            return <ol className="list-decimal pl-5 my-2">{children}</ol>;
          },
          blockquote({ children }) {
            return (
              <blockquote className="border-l-4 pl-3 italic text-gray-700 my-2">
                {children}
              </blockquote>
            );
          },
          h1: (p) => <h1 className="font-semibold text-xl mt-3 mb-1" {...p} />,
          h2: (p) => <h2 className="font-semibold text-lg mt-3 mb-1" {...p} />,
          h3: (p) => <h3 className="font-semibold mt-3 mb-1" {...p} />,
          table: (p) => (
            <div className="overflow-x-auto my-2">
              <table className="min-w-full text-sm border" {...p} />
            </div>
          ),
          th: (p) => <th className="border px-2 py-1 bg-gray-50" {...p} />,
          td: (p) => <td className="border px-2 py-1" {...p} />,
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
}
