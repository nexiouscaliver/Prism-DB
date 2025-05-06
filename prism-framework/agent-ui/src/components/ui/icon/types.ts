import { type IconType as ReactIconType } from 'react-icons'

export type IconSize = 'xxs' | 'xs' | 'sm' | 'md' | 'lg' | 'dot' | 'default'

export type IconType = 
  | 'open-ai'
  | 'gemini'
  | 'mistral'
  | 'aws'
  | 'azure'
  | 'anthropic'
  | 'groq'
  | 'fireworks'
  | 'deepseek'
  | 'cohere'
  | 'ollama'
  | 'xai'
  | 'agno'
  | 'user'
  | 'agent'
  | 'sheet'
  | 'nextjs'
  | 'shadcn'
  | 'tailwind'
  | 'reasoning'
  | 'prism-tag'
  | 'refresh'
  | 'edit'
  | 'save'
  | 'x'
  | 'arrow-down'
  | 'send'
  | 'download'
  | 'hammer'
  | 'check'
  | 'chevron-down'
  | 'chevron-up'
  | 'plus-icon'
  | 'references'
  | 'trash'
  | 'python'

export interface IconProps {
  type: IconType
  size?: IconSize
  className?: string
  color?: string
  disabled?: boolean
}

export type IconComponent = ReactIconType
