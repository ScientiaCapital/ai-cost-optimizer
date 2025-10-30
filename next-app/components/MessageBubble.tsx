import type { FC, PropsWithChildren } from 'react'

type Props = PropsWithChildren<{ role: 'user' | 'assistant' }>

export const MessageBubble: FC<Props> = ({ role, children }) => {
  const isUser = role === 'user'
  return (
    <div className={isUser ? 'flex justify-end' : 'flex justify-start'}>
      <div
        className={
          'max-w-[85%] whitespace-pre-wrap rounded-lg px-3 py-2 text-sm ' +
          (isUser ? 'bg-blue-600 text-white' : 'bg-white text-gray-900 shadow')
        }
        role="article"
        aria-label={isUser ? 'User message' : 'Assistant message'}
      >
        {children}
      </div>
    </div>
  )
}
