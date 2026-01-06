Feature: mcodex init

  Scenario: Init creates repo config, templates, and updates gitignore
    When I run "mcodex init"
    Then a file ".mcodex/config.yaml" exists
    And a directory ".mcodex/templates" exists
    And a directory ".mcodex/templates/text" exists
    And a directory ".mcodex/templates/latex" exists
    And a directory ".mcodex/templates/pandoc" exists
    And a file ".mcodex/templates/text/todo.md" exists
    And a file ".mcodex/templates/text/checklist.md" exists
    And a file ".mcodex/templates/text/README.txt" exists
    And a file ".mcodex/templates/latex/main.tex" exists
    And a file ".mcodex/templates/pandoc/reference.docx" exists
    And a file ".mcodex/templates/pandoc/template.tex" exists
    And the file ".gitignore" contains "artifacts/"
