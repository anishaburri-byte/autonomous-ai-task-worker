export default function Timeline({events,status}:{events:any[],status:string}){
  return (
    <div className="mt-6">
      <h2 className="font-semibold">Execution Timeline — {status}</h2>
      {events.length===0 && <p className="text-gray-400 text-sm mt-2">No events yet. Submit a task.</p>}
      <ul className="mt-2 space-y-1">
        {events.map((e,i)=>(
          <li key={i} className="text-sm border-l-2 pl-2 py-1" style={{borderColor: e.status==="success"?"#16a34a": e.status==="failure"?"#dc2626":"#9ca3af"}}>
            <span className="font-mono">{e.tool}</span> — {e.status} {e.duration_ms?`(${e.duration_ms}ms)`:""} {e.retry?`retry=${e.retry}`:""}
          </li>
        ))}
      </ul>
      {status==="awaiting_clarification" && <p className="text-amber-600 text-sm mt-2">Awaiting human clarification (OCR low confidence)</p>}
      {status==="completed" && <p className="text-green-600 text-sm mt-2">✓ Verified completed</p>}
      {status==="failed" && <p className="text-red-600 text-sm mt-2">✗ Failed — see events</p>}
    </div>
  )
}
