// src/dummyData.js
import { reactive } from 'vue'
import { v4 as uuidv4 } from 'uuid'

/**
 * 1) contracts: Example “contracts” (id + name).
 * 2) dataItems: Example “payloads” that could be shared.
 * 3) issuedAttestations: In-memory store for attestations this participant has issued.
 * 4) requestedAttestations: In-memory store for attestations this participant has requested from others.
 *
 * Each attestation: {
 *   id, dataItemId, contractId, evaluationResults, passed, issuedAt | requestedAt,  // timestamps
 *   requesterId?, issuerId?  // optional fields to distinguish request vs. actual issuance
 * }
 */

export const contracts = reactive([
  { id: 'contract-A', name: 'Contract A: JSON Schema v1' },
  { id: 'contract-B', name: 'Contract B: Timestamp ≤ 7 days' },
  { id: 'contract-C', name: 'Contract C: Unique userId' }
])

export const dataItems = reactive([
  {
    id: 'data-1',
    contractId: 'contract-A',
    payload: { userId: 'alice', event: 'login', timestamp: '2025-06-03T08:15:00Z' }
  },
  {
    id: 'data-2',
    contractId: 'contract-B',
    payload: { userId: 'bob', event: 'purchase', timestamp: '2025-05-20T12:00:00Z' }
  },
  {
    id: 'data-3',
    contractId: 'contract-C',
    payload: [
      { userId: 'carol', score: 42 },
      { userId: 'dave', score: 37 },
      { userId: 'carol', score: 55 } // duplicate userId on purpose
    ]
  }
])

// 1) Attestations this participant has issued
export const issuedAttestations = reactive([])

// 2) Attestations this participant has requested from others
export const requestedAttestations = reactive([
  // Dummy pre‐populated “requested” attestations to illustrate the UI
  {
    id: uuidv4(),
    dataItemId: 'data-2',
    contractId: 'contract-B',
    evaluationResults: [ { aspect: 'Timestamp ≤ 7 days', result: 'failed', reason: 'Age = 14 days' } ],
    passed: false,
    requestedAt: '2025-06-05T10:15:00Z',
    issuerId: 'other-participant-1'
  },
  {
    id: uuidv4(),
    dataItemId: 'data-3',
    contractId: 'contract-C',
    evaluationResults: [ { aspect: 'Unique userId', result: 'failed', reason: 'Duplicate userId = carol' } ],
    passed: false,
    requestedAt: '2025-06-06T09:30:00Z',
    issuerId: 'other-participant-2'
  }
])

/**
 * Helper to “issue” a new attestation (simulating the provider‐side issuance).
 * We push into issuedAttestations. In a real scenario, this would be a backend call.
 */
export function issueAttestation(dataItemId, contractId) {
  const item = dataItems.find(d => d.id === dataItemId)
  if (!item) {
    throw new Error(`DataItem ${dataItemId} not found`)
  }

  let evaluationResults = []
  let passed = true

  if (contractId === 'contract-A') {
    try {
      JSON.parse(JSON.stringify(item.payload))
      evaluationResults.push({ aspect: 'JSON Schema v1', result: 'passed' })
    } catch (e) {
      passed = false
      evaluationResults.push({ aspect: 'JSON Schema v1', result: 'failed', reason: e.message })
    }
  }
  else if (contractId === 'contract-B') {
    const now = new Date()
    const ts = new Date(item.payload.timestamp)
    const diffDays = Math.floor((now - ts) / (1000 * 60 * 60 * 24))
    if (diffDays <= 7) {
      evaluationResults.push({ aspect: 'Timestamp ≤ 7 days', result: 'passed' })
    } else {
      passed = false
      evaluationResults.push({ aspect: 'Timestamp ≤ 7 days', result: 'failed', reason: `Age = ${diffDays} days` })
    }
  }
  else if (contractId === 'contract-C') {
    const seen = new Set()
    for (const record of item.payload) {
      if (seen.has(record.userId)) {
        passed = false
        evaluationResults.push({ aspect: 'Unique userId', result: 'failed', reason: `Duplicate userId = ${record.userId}` })
        break
      }
      seen.add(record.userId)
    }
    if (passed) {
      evaluationResults.push({ aspect: 'Unique userId', result: 'passed' })
    }
  }

  const newAtt = {
    id: uuidv4(),
    dataItemId,
    contractId,
    evaluationResults,
    passed,
    issuedAt: new Date().toISOString(),
    requesterId: 'self',      // “self” indicates I issued it
    issuerId: 'self'
  }

  issuedAttestations.push(newAtt)
  return newAtt
}

/**
 * Helper to “request” an attestation from others (simulating consumer‐side).
 * We push into requestedAttestations. In reality, this calls out to a provider.
 */
export function requestAttestation(dataItemId, contractId) {
  const item = dataItems.find(d => d.id === dataItemId)
  if (!item) {
    throw new Error(`DataItem ${dataItemId} not found`)
  }

  // For this dummy, we’ll simulate a “successful” attestation from someone else:
  const simulatedResult = [
    { aspect: contractId === 'contract-A' ? 'JSON Schema v1' : (contractId === 'contract-B' ? 'Timestamp ≤ 7 days' : 'Unique userId'),
      result: 'passed' }
  ]
  const passed = true

  const newReq = {
    id: uuidv4(),
    dataItemId,
    contractId,
    evaluationResults: simulatedResult,
    passed,
    requestedAt: new Date().toISOString(),
    requesterId: 'self',
    issuerId: 'other-participant-demo'
  }

  requestedAttestations.push(newReq)
  return newReq
}

/**
 * Helper to “verify” an attestation (common for both issued & requested).
 * We simply return `passed` === true. In a real system you'd check a signature or proof.
 */
export function verifyAttestation(attestationId) {
  const all = [...issuedAttestations, ...requestedAttestations]
  const att = all.find(a => a.id === attestationId)
  if (!att) return false
  return att.passed
}
