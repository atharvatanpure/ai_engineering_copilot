export default function CodeViewer({
  filePath,
  content,
  highlightStart,
  highlightEnd,
}: {
  filePath: string;
  content: string;
  highlightStart?: number;
  highlightEnd?: number;
}) {
  const lines = content.split("\n");

  return (
    <div className="overflow-hidden rounded-md border border-border bg-surface">
      <div className="mono flex items-center justify-between border-b border-border bg-surface-alt px-4 py-2 text-xs text-muted">
        <span>{filePath}</span>
        {highlightStart && highlightEnd && (
          <span>
            lines {highlightStart}–{highlightEnd}
          </span>
        )}
      </div>
      <div className="scrollbar-thin mono max-h-[520px] overflow-auto text-[13px] leading-6">
        <table className="w-full border-collapse">
          <tbody>
            {lines.map((line, idx) => {
              const lineNo = idx + 1;
              const isHighlighted =
                highlightStart && highlightEnd && lineNo >= highlightStart && lineNo <= highlightEnd;
              return (
                <tr
                  key={lineNo}
                  className={isHighlighted ? "bg-accent/10" : ""}
                >
                  <td className="select-none border-r border-border px-3 py-0 text-right text-muted">
                    {lineNo}
                  </td>
                  <td className="whitespace-pre px-4 py-0 text-[#e6e8ef]">{line || " "}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
