import React, { useEffect, useState } from 'react';

const API = process.env.REACT_APP_API_URL;

export default function LeadFlowPage() {
  const [flows, setFlows] = useState([]);
  useEffect(() => {
    fetch(`${API}/lms/lead-flow/all`).then((r) => r.json()).then(setFlows);
  }, []);
  return (
    <div className="lead-flows">
      {flows.map((f) => <span key={f.id}>{f.name as string}</span>)}
    </div>
  );
}
