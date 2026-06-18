Feature: Veracity Level Agreement (VLA) management
  As a user of the dataspace
  I want to create/query VLAs for my data exchanges

  Background:
    # Could be any DVA service, we just use provider
    Given url 'http://dva-api-provider:9090'
    * def exampleTemplate = read('../test-data/vla-template/template.json')
    * def exampleVLARequest = read('../test-data/vla-request/request.json')
    * def exampleVLARequestFromTemplates = read('../test-data/vla-request/request-from-templates.json')

  Scenario: get all VLAs
    Given path 'vla'
    When method get
    Then status 200

  Scenario: create and retrieve VLA
    Given path 'vla'
    And request exampleVLARequest
    When method post
    Then status 201
    And match response == { id: '#string' }
    * def id = response.id

    Given path 'vla', id
    When method get
    Then status 200
    And match response contains exampleVLARequest

  Scenario: create VLA from templates and then retrieve it
    Given path 'template'
    And request exampleTemplate
    When method post
    Then status 201
    * def templateID = response.id

    Given path 'vla', 'from-templates'
    And request karate.merge(exampleVLARequestFromTemplates, { qualityTemplates: [{ id: templateID, model: { date: '20250101' } }] })
    When method post
    Then status 201
    * def id = response.id

    Given path 'vla', id
    When method get
    Then status 200
    And match response.quality contains { engine: 'JQ', implementation: "{ success: .date == '20250101' }" }

    Given path 'template', templateID
    When method delete
    Then status 204
