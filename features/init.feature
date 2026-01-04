Feature: mcodex init

  Scenario: Init creates repo config, templates, and updates gitignore
    When I run "mcodex init"
    Then a file ".mcodex/config.yaml" exists
    And a directory ".mcodex/templates" exists
    And the file ".gitignore" contains "artifacts/"

