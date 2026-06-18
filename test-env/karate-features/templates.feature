Feature: Veracity Level Agreement (VLA) template management
  As an administrator / dataspace orchestrator
  I want to create/update/delete available templates that can be used in VLAs

  Background:
    # Could be any DVA service, we just use provider
    Given url 'http://dva-api-provider:9090/template'
    * def exampleTemplate = read('../test-data/vla-template/template.json')

  Scenario: get all VLA templates
    When method get
    Then status 200

  Scenario: create, get, then delete VLA template
    Given request exampleTemplate
    When method post
    Then status 201
    And match response == { id: '#string' }
    * def id = response.id

    Given path id
    When method get
    Then status 200
    And match response == karate.merge(exampleTemplate, { id: id })
    * def templateWithID = response

    When method get
    Then status 200
    And match response contains templateWithID

    Given path id
    When method delete
    Then status 204

  Scenario: create, render, then delete VLA template
    Given request exampleTemplate
    When method post
    Then status 201
    * def id = response.id

    Given path id, 'render'
    And request { date: '20250101' }
    When method post
    Then status 200
    And match response == { engine: 'JQ', implementation: "{ success: .date == '20250101' }" }

    Given path id
    When method delete
    Then status 204
