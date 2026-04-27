/**
 * SceneStage — full-bleed cinematic image with crossfade + Ken Burns drift.
 * Shows a shimmer placeholder while no image is loaded yet.
 */
import { AnimatePresence, motion } from 'framer-motion'

interface Props {
  imageUrl: string
  altText: string
  isLoading?: boolean
  /** Optional desaturation overlay for dire world states */
  desaturate?: boolean
}

export default function SceneStage({ imageUrl, altText, isLoading, desaturate }: Props) {
  return (
    <div className="relative w-full h-full overflow-hidden rounded-xl bg-ogma-surface">
      {/* Shimmer placeholder */}
      {(!imageUrl || isLoading) && (
        <div className="absolute inset-0 bg-gradient-to-br from-ogma-surface to-ogma-surface2 animate-pulse" />
      )}

      {/* Main image with crossfade */}
      <AnimatePresence mode="crossfade">
        {imageUrl && (
          <motion.div
            key={imageUrl}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
            className="absolute inset-0"
          >
            {/* Ken Burns zoom */}
            <motion.img
              src={imageUrl}
              alt={altText}
              className="w-full h-full object-cover"
              animate={{ scale: [1, 1.04] }}
              transition={{ duration: 8, ease: 'linear', repeat: Infinity, repeatType: 'reverse' }}
            />

            {/* Desaturation overlay */}
            {desaturate && (
              <motion.div
                className="absolute inset-0 bg-ogma-bg/40 backdrop-grayscale"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 1 }}
              />
            )}

            {/* Bottom gradient for text readability */}
            <div className="absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-ogma-bg/90 to-transparent pointer-events-none" />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
