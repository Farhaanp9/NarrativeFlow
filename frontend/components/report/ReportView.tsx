import ReactMarkdown from "react-markdown";

interface ReportViewProps {
  content: string;
}

export function ReportView({ content }: ReportViewProps) {
  return (
    <div className="prose prose-invert prose-sm max-w-none">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}
