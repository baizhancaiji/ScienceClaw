/**
 * Markdown 格式化工具
 * 对 LLM 输出的 Markdown 进行预处理和清理
 */

/**
 * 预处理 Markdown 文本，修复 LLM 输出中的常见格式问题
 * @param text 原始 Markdown 文本
 * @returns 格式化后的 Markdown 文本
 */
export function formatMarkdown(text: string): string {
  if (!text || typeof text !== 'string') {
    return '';
  }
  return preprocessMarkdown(text);
}

/**
 * 同步版本（与异步版本相同，保持 API 兼容）
 */
export function formatMarkdownSync(text: string): string {
  return formatMarkdown(text);
}

/**
 * 预处理：清理 LLM 输出中的常见问题
 */
function preprocessMarkdown(text: string): string {
  let result = text;

  // 先将代码块和行内代码保护起来，避免后续正则误改代码内容
  const codeSegments: string[] = [];
  let codeSegCounter = 0;
  const protectCode = (segment: string) => {
    const id = `__SCFMT_CODE_${codeSegCounter++}__`;
    codeSegments.push(segment);
    return id;
  };

  // 保护围栏代码块
  const fenceRegex = /^(```|~~~)/gm;
  let fenceMatch: RegExpExecArray | null;
  const fencePositions: { start: number; end: number }[] = [];
  while ((fenceMatch = fenceRegex.exec(result)) !== null) {
    const fence = fenceMatch[1];
    const startPos = fenceMatch.index;
    const closeRegex = new RegExp(`^${fence}`, 'gm');
    closeRegex.lastIndex = startPos + fence.length;
    const closeMatch = closeRegex.exec(result);
    if (closeMatch) {
      fencePositions.push({ start: startPos, end: closeMatch.index + closeMatch[0].length });
      fenceRegex.lastIndex = closeMatch.index + closeMatch[0].length;
    } else {
      fencePositions.push({ start: startPos, end: result.length });
      break;
    }
  }

  // 从后往前替换代码块
  for (let i = fencePositions.length - 1; i >= 0; i--) {
    const { start, end } = fencePositions[i];
    const segment = result.substring(start, end);
    result = result.substring(0, start) + protectCode(segment) + result.substring(end);
  }

  // 保护行内代码
  result = result.replace(/`[^`\n]+`/g, protectCode);

  // 1. 修复连续的空行（超过2个空行压缩为2个）
  result = result.replace(/\n{3,}/g, '\n\n');

  // 2. 统一列表标记为 -
  result = result.replace(/^(\s*)[*+]\s/gm, '$1- ');

  // 3. 修复列表项的多余空格
  result = result.replace(/^(\s*)-\s{2,}/gm, '$1- ');

  // 4. 修复有序列表的空格
  result = result.replace(/^(\s*)(\d+)\.\s{2,}/gm, '$1$2. ');

  // 5. 确保标题前后有适当的空行
  result = result.replace(/([^\n])\n(#{1,6}\s)/g, '$1\n\n$2');
  result = result.replace(/(^#{1,6}\s[^\n]+)\n([^\n#])/gm, '$1\n\n$2');

  // 6. 修复代码块的语言标识符（在保护段内已被保护，此步仅处理未被保护的场景）
  result = result.replace(/```(\w+)(\s*)\n/g, (_, lang) => '```' + lang.toLowerCase() + '\n');

  // 7. 修复行内代码的多余空格
  result = result.replace(/`\s+([^`]+?)\s+`/g, '`$1`');

  // 8. 修复链接格式
  result = result.replace(/\[([^\]]+)\]\s*\(\s*([^)\s]+)\s*\)/g, '[$1]($2)');

  // 9. 确保代码块闭合
  const codeBlockCount = (result.match(/```/g) || []).length;
  if (codeBlockCount % 2 !== 0) {
    result += '\n```';
  }

  // 10. 移除标点符号前的多余空格
  result = result.replace(/\s+([.,!?;:])/g, '$1');

  // 11. 修复表格格式
  result = normalizeTables(result);

  // 12. 确保引用块格式正确
  result = result.replace(/^>(\s*)(\S)/gm, '> $2');

  // 恢复代码段
  for (let i = codeSegments.length - 1; i >= 0; i--) {
    result = result.replace(`__SCFMT_CODE_${i}__`, codeSegments[i]);
  }

  return result.trim();
}

/**
 * 规范化表格格式
 */
function normalizeTables(text: string): string {
  const lines = text.split('\n');
  const result: string[] = [];
  let inTable = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const isTableRow = /^\|.*\|$/.test(line.trim());
    // Split the character class so Tailwind does not misread it as an arbitrary CSS class.
    const tableDividerPattern = new RegExp('^\\|[-:' + '\\s|]+\\|$');
    const isTableDivider = tableDividerPattern.test(line.trim());

    if (isTableRow || isTableDivider) {
      if (!inTable) {
        // 确保表格前有空行
        if (result.length > 0 && result[result.length - 1].trim() !== '') {
          result.push('');
        }
        inTable = true;
      }
      result.push(line);
    } else {
      if (inTable) {
        // 确保表格后有空行
        if (line.trim() !== '') {
          result.push('');
        }
        inTable = false;
      }
      result.push(line);
    }
  }

  return result.join('\n');
}

/**
 * 清理 Markdown 中的 XML 标签（如 <suggested_questions>）
 */
export function extractXmlTags(text: string): {
  cleanedText: string;
  tags: Record<string, string>;
} {
  const tags: Record<string, string> = {};
  let cleanedText = text;

  // 提取并移除 suggested_questions 标签
  const suggestionRegex = /<suggested_questions>([\s\S]*?)<\/suggested_questions>/;
  const match = cleanedText.match(suggestionRegex);
  if (match) {
    tags.suggested_questions = match[1];
    cleanedText = cleanedText.replace(suggestionRegex, '');
  }

  return { cleanedText, tags };
}

export default {
  formatMarkdown,
  formatMarkdownSync,
  extractXmlTags,
};
