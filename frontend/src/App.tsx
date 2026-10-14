import { useState, useEffect } from 'react'
import Timeline from './components/Timeline.tsx'

const API = "http://localhost:8000"

export default function App(){
  const [token,setToken]=useState(localStorage.getItem("token")||"")
  const [goal,setGoal]=useState("Find the latest invoice from Acme Corporation, extract invoice number, amount, currency, due date, enter into finance system and tell me when done.")
  const [taskId,setTaskId]=useState<number|null>(null)
  const [status,setStatus]=useState("")
  const [events,setEvents]=useState<any[]>([])
  const [user,setUser]=useState("demo-user")

  const login=async()=>{
    const r=await fetch(`${API}/api/auth/login`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({user})})
    const j=await r.json()
    localStorage.setItem("token",j.token)
    setToken(j.token)
  }

  const createTask=async()=>{
    const r=await fetch(`${API}/api/tasks`,{method:"POST",headers:{"Content-Type":"application/json","Authorization":`Bearer ${token}`},body:JSON.stringify({goal})})
    const j=await r.json()
    setTaskId(j.id)
    setStatus("pending")
    setEvents([])
  }

  useEffect(()=>{
    if(!taskId || !token) return
    const es=new EventSource(`${API}/api/tasks/${taskId}/stream?token=${token}`)
    // Note: EventSource cannot send headers, backend also checks query param fallback if implemented, else use fetch streaming
    es.onmessage=(e)=>{
      if(e.data=="[DONE]"){ es.close(); return }
      try{
        const d=JSON.parse(e.data)
        if(d.tool) setEvents(prev=>[...prev,d])
        if(d.status) setStatus(d.status)
      }catch{}
    }
    return ()=>es.close()
  },[taskId, token])

  const approve=async()=>{
    const t=await fetch(`${API}/api/tasks/${taskId}/approval_token`,{headers:{"Authorization":`Bearer ${token}`}})
    const {approval_token}=await t.json()
    await fetch(`${API}/api/tasks/${taskId}/approve`,{method:"POST",headers:{"Content-Type":"application/json","Authorization":`Bearer ${token}`},body:JSON.stringify({approval_token})})
  }

  if(!token) return (
    <div className="p-8 max-w-xl mx-auto">
      <h1 className="text-2xl font-bold">AI Worker v3</h1>
      <input value={user} onChange={e=>setUser(e.target.value)} placeholder="user" className="border p-2 w-full mt-4" />
      <button onClick={login} className="bg-black text-white px-4 py-2 mt-2">Login</button>
    </div>
  )

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold">Autonomous AI Task Worker</h1>
      <p className="text-sm text-gray-500">Model: {status||"idle"} | Task: {taskId||"none"}</p>
      <textarea value={goal} onChange={e=>setGoal(e.target.value)} className="border w-full p-2 h-24 mt-4" />
      <div className="flex gap-2 mt-2">
        <button onClick={createTask} className="bg-black text-white px-4 py-2">Run Task</button>
        {status==="awaiting_approval" && <button onClick={approve} className="bg-green-600 text-white px-4 py-2">Approve</button>}
        <button onClick={()=>{localStorage.clear(); setToken("")}} className="border px-4 py-2">Logout</button>
      </div>
      <Timeline events={events} status={status} />
    </div>
  )
}
