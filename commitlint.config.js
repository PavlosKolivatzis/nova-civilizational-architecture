// commitlint.config.js
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    // core hygiene
    'header-max-length': [2, 'always', 72],
    'body-max-line-length': [2, 'always', 100],
    'type-empty': [2, 'never'],
    'subject-empty': [2, 'never'],
    'scope-case': [2, 'always', 'kebab-case'],

    // require lowercase subjects (your CI complained about "MLS")
    'subject-case': [2, 'always', ['lower-case']],

    // conventional types you actually use
    'type-enum': [
      2,
      'always',
      [
        'feat',
        'fix',
        'docs',
        'style',
        'refactor',
        'perf',
        'test',
        'build',
        'ci',
        'chore',
        'revert'
      ]
    ]
  }
};