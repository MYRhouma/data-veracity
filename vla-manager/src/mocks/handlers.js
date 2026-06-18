import { http, HttpResponse } from 'msw'
import { v4 as uuid } from 'uuid'
import { renderTemplate } from './templates'

const vlas = [
  {
    id: uuid(),
    description: 'Mocked VLA one',
    quality: [
      {
        engine: 'JQ',
        implementation: '.foo == .bar'
      }
    ]
  },
  {
    id: uuid(),
    description: 'Mocked VLA two',
    quality: [
      {
        engine: 'GREAT_EXPECTATIONS',
        implementation: '... great expectations yaml ...'
      }
    ]
  }
]

const templates = [
  {
    id: uuid(),
    name: 'JSON schema (mock)',
    description: 'Mock template for JSON schema compliance',
    criterionType: 'VALID_INVALID',
    targetAspect: 'SYNTAX',
    evaluationMethod: {
      engine: 'SCHEMA',
      variableSchema: {
        properties: {
          schemaURL: { type: 'string' }
        }
      },
      implementationTemplate: '{{ schemaURL }}'
    }
  },
  {
    id: uuid(),
    name: 'Property value in range (mock)',
    description: 'Mock template for a GE-based range check',
    criterionType: 'IN_RANGE',
    targetAspect: 'ACCURACY',
    evaluationMethod: {
      engine: 'GREAT_EXPECTATIONS',
      variableSchema: {
        properties: {
          property: { type: "string" },
          minimum: { type: "string" },
          maximum: { type: "string" }
        }
      },
      implementationTemplate: "---\ntype: ExpectColumnValuesToBeBetween\nkwargs:\n  column: {{ property }}\n  min_value: '{{ minimum }}'\n  max_value: '{{ maximum }}'\nmeta:\n  schema:\n    columns:\n      {{ property }}:\n...\n"
    }
  }
]

let vlaCounter = 1

export const handlers = [
  http.get('/api/template', () => {
    console.log('Returning mock template list')
    return HttpResponse.json(templates)
  }),

  http.get('/api/vla', () => {
    console.log('Returning mock VLA list')
    return HttpResponse.json(vlas)
  }),

  http.post('/api/vla/from-templates', async ({ request }) => {
    const body = await request.json()
    console.log('Mock backend received VLA from-templates request:')
    console.log(body)

    const vla = {
      description: `Mock-generated VLA ${vlaCounter++}: ${request.description}`,
      quality: request.qualityTemplates.map(({ id, model }) => {
        const template = templates.find((t) => t.id === id)
        if (template === undefined) {
          console.error(`Mock backend could not find template ${id}`)
          return HttpResponse(null, { status: 404 })
        }

        return HttpResponse.json(renderTemplate(template, model))
      })
    }
    vlas.push(vla)
    console.log('Returning mock response for /api/vla/from-templates request:')
    console.log(vla)

    return HttpResponse.json(vla)
  }),

  http.post('/api/attestation', async ({ request }) => {
    const body = await request.json()
    console.log('Mock backend received /attestation request:')
    console.log(body)

    const resp = HttpResponse.json({ id: uuid() }, { status: 202 })
    console.log('Returning mock response for /attestation request:')
    console.log(resp)

    return resp
  }),
  
  http.post('/api/evaluate/from-template', async ({ request }) => {
    const body = await request.json()
    console.log('Mock backend received /evaluate/from-template request:')
    console.log(body)

    const { templateID, templateModel, data } = body
    const template = templates.find((t) => t.id === templateID)
    if (template === undefined) {
      console.error(`Mock backend could not find template ${id}`)
      return HttpResponse(null, { status: 404 })
    }

    const resp = {
      engine: template.evaluationMethod.engine,
      timestamp: new Date().toISOString(),
      success: Math.random() < 0.5,
      details: '(mock evaluation details)'
    }
    console.log('Returning mock response for /evaluate/from-template request:')
    console.log(resp)

    return HttpResponse.json(resp)
  })
]
