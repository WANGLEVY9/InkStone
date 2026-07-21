import matter from 'gray-matter';

export interface FrontmatterData {
  [key: string]: unknown;
}

export const parseFrontmatter = (content: string): { data: FrontmatterData; body: string } => {
  const { data, content: body } = matter(content);
  return { data, body };
};

export const serializeWithFrontmatter = (data: FrontmatterData, body: string): string => {
  return matter.stringify(body, data);
};

export const parseCharacterMeta = (content: string) => {
  const { data, body } = parseFrontmatter(content);
  return {
    tags: (data.tags as string[]) || [],
    type: (data.type as string) || '',
    age: (data.age as string) || '',
    content: body,
  };
};
