import { fileURLToPath } from 'node:url';
import { apply as registerFilesystemSkills } from '@deepseek-ai/dsh-skill-filesystem';

// Register the skills shipped with the plugin in DSH's host-wide registry.
// User and project skills retain their normal higher priority.
export const inject = ['skills'];
export function apply(ctx) {
  registerFilesystemSkills(ctx, {
    providerName: 'finfreedom-bundled',
    includeDefaultRoots: false,
    watch: false,
    bundledSkillDir: fileURLToPath(new URL('../skills/', import.meta.url)),
  });
}
