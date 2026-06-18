import hb from 'handlebars'

export function renderTemplate(template, model) {
  console.log('Mock-rendering a template')
  const implTempl = hb.compile(template.implementationTemplate)
  return {
    engine: template.engine,
    implementation: implTempl(model)
  }
}
