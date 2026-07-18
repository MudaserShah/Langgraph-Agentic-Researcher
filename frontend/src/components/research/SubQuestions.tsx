/**
 * SubQuestions.tsx — Renders the 3 sub-question pills at the top of the report.
 *
 * These show the student EXACTLY how the agent broke down the research topic
 * into targeted search queries.
 */

interface SubQuestionsProps {
  questions: string[]
}

export function SubQuestions({ questions }: SubQuestionsProps) {
  if (questions.length === 0) return null

  return (
    <div className="mb-6 p-4 bg-indigo-50 border border-indigo-100 rounded-xl">
      <p className="text-xs font-semibold text-indigo-700 uppercase tracking-wide mb-2.5">
        Research Sub-questions
      </p>
      <div className="flex flex-col gap-2">
        {questions.map((q, i) => (
          <div key={i} className="flex items-start gap-2">
            <span className="flex-shrink-0 w-5 h-5 rounded-full bg-indigo-600 text-white text-xs font-bold flex items-center justify-center mt-0.5">
              {i + 1}
            </span>
            <span className="text-indigo-800 text-sm leading-snug">{q}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
