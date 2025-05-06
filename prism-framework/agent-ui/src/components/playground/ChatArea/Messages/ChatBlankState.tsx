'use client'

import Link from 'next/link'
import { motion, Variants } from 'framer-motion'
import Icon from '@/components/ui/icon'
import { IconType } from '@/components/ui/icon/types'
import React, { useState } from 'react'
import { IconContext } from 'react-icons'

interface TechIcon {
  type: IconType;
  position: string;
  link: string;
  name: string;
  zIndex: number;
  className?: string;
}

const EXTERNAL_LINKS = {
  documentation: 'https://agno.link/agent-ui',
  playground: 'https://app.agno.com/playground/agents',
  prism: 'https://github.com/nexiouscaliver/Prism-DB'
}

const TECH_ICONS: TechIcon[] = [
  {
    type: 'python' as IconType,
    position: 'left-[1px]',
    link: 'https://python.org',
    name: 'Python',
    zIndex: 10,
    // className: 'text-primary fill-current'
  },
  {
    type: 'tailwind' as IconType,
    position: 'left-[15px]',
    link: 'https://tailwindcss.com',
    name: 'Tailwind CSS',
    zIndex: 20
  },
  {
    type: 'nextjs' as IconType,
    position: 'left-[30px]',
    link: 'https://nextjs.org',
    name: 'Next.js',
    zIndex: 30
  }
]

interface ActionButtonProps {
  href: string
  variant?: 'primary'
  text: string
}

const ActionButton = ({ href, variant, text }: ActionButtonProps) => {
  const baseStyles =
    'px-4 py-2 text-sm transition-colors font-dmmono tracking-tight'
  const variantStyles = {
    primary: 'border border-border hover:bg-neutral-800 rounded-xl'
  }

  return (
    <Link
      href={href}
      target="_blank"
      className={`${baseStyles} ${variant ? variantStyles[variant] : ''}`}
    >
      {text}
    </Link>
  )
}

const ChatBlankState = () => {
  const [hoveredIcon, setHoveredIcon] = useState<string | null>(null)

  // Animation variants for the icon
  const iconVariants: Variants = {
    initial: { y: 0 },
    hover: {
      y: -8,
      transition: {
        type: 'spring',
        stiffness: 150,
        damping: 10,
        mass: 0.5
      }
    },
    exit: {
      y: 0,
      transition: {
        type: 'spring',
        stiffness: 200,
        damping: 15,
        mass: 0.6
      }
    }
  }

  // Animation variants for the tooltip
  const tooltipVariants: Variants = {
    hidden: {
      opacity: 0,
      transition: {
        duration: 0.15,
        ease: 'easeInOut'
      }
    },
    visible: {
      opacity: 1,
      transition: {
        duration: 0.15,
        ease: 'easeInOut'
      }
    }
  }

  return (
    <section
      className="flex flex-col items-center text-center font-geist"
      aria-label="Welcome message"
    >
      <div className="flex max-w-3xl flex-col gap-y-8">
        <motion.h1
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="text-3xl font-[600] tracking-tight"
        >
          <div className="flex items-center justify-center gap-x-2 whitespace-nowrap font-medium">
            <span className="flex items-center font-[600]">
              This is PrismDB
            </span>
            {/* <Link
              href={EXTERNAL_LINKS.prism}
              target="_blank"
              rel="noopener"
              className="flex items-center px-1 py-1 rounded-md bg-gray-200 hover:bg-gray-300 transition-colors text-black"
            >
              <span className="text-xs mr-1">PrismDB</span>
              <Icon type="prism-tag" size="xs" />
            </Link> */}
            <span className="flex items-center font-[600]">
              Agent UI, built with
            </span>
            <span className="inline-flex translate-y-[5px] scale-125 items-center">
              <div className="relative ml-2 h-[40px] w-[90px]">
                {TECH_ICONS.map((icon) => (
                  <motion.div
                    key={icon.type}
                    className={`absolute ${icon.position} top-0`}
                    style={{ zIndex: icon.zIndex }}
                    variants={iconVariants}
                    initial="initial"
                    whileHover="hover"
                    animate={hoveredIcon === icon.type ? 'hover' : 'exit'}
                    onHoverStart={() => setHoveredIcon(icon.type)}
                    onHoverEnd={() => setHoveredIcon(null)}
                  >
                    <Link
                      href={icon.link}
                      target="_blank"
                      rel="noopener"
                      className="relative block cursor-pointer"
                    >
                      <div>
                        <Icon 
                          type={icon.type} 
                          size="default" 
                          className={icon.className}
                        />
                      </div>
                      <motion.div
                        className="pointer-events-none absolute bottom-full left-1/2 mb-1 -translate-x-1/2 transform whitespace-nowrap rounded bg-neutral-800 px-2 py-1 text-xs text-primary"
                        variants={tooltipVariants}
                        initial="hidden"
                        animate={
                          hoveredIcon === icon.type ? 'visible' : 'hidden'
                        }
                      >
                        {icon.name}
                      </motion.div>
                    </Link>
                  </motion.div>
                ))}
              </div>
            </span>
          </div>
          <p>Explore the power of PrismDB - your database made smarter.</p>
        </motion.h1>
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="flex justify-center gap-4"
        >
          {/* <ActionButton
            href={EXTERNAL_LINKS.documentation}
            variant="primary"
            text="GO TO PRISM DOCS"
          />
          <ActionButton
            href={EXTERNAL_LINKS.playground}
            text="VISIT AGENT PLAYGROUND"
          /> */}
        </motion.div>
      </div>
    </section>
  )
}

export default ChatBlankState
