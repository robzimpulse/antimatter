## Description
<!-- Please include a summary of the change and which issue is fixed. Include relevant motivation and context. -->

Fixes # (issue number)

## Type of Change
<!-- Please delete options that are not relevant. -->
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Security patch

## Security & Compliance Checklist
> [!WARNING]
> **STRICT ENFORCEMENT:** Antimatter integrates directly with the user's host machine at the IDE level. Any Pull Request that fails to check these boxes, or falsely checks these boxes, will be automatically closed and the contributor may be banned. You MUST read and verify each point.

- [ ] I have verified that no proprietary dependencies (e.g., Google Play Services, Firebase) have been added to the `foss` flavor.
- [ ] Any new file system hooks or operations include strict path normalization and respect sandbox boundaries.
- [ ] Any incoming strings/data are strictly sanitized before being passed to the IDE or Android App.
- [ ] I have not added any `.so`, `.jar`, or `.aar` pre-compiled binaries.

## Testing Checklist
- [ ] My code follows the style guidelines of this project (ktlint/detekt for Android, ESLint for TypeScript).
- [ ] I have performed a self-review of my own code.
- [ ] I have commented my code, particularly in hard-to-understand reverse-engineering hooks.
- [ ] I have made corresponding changes to the documentation (`README.md`, `ARCHITECTURE.md`, `CHANGELOG.md`).
- [ ] I have verified my changes compile under both `standard` and `foss` Android flavors.

## Screenshots (if applicable)
<!-- If this PR changes the Android UI, please provide screenshots or a video recording. -->
