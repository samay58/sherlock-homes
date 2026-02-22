import { useState } from 'react'
import './ImageGallery.css'

interface ImageGalleryProps {
  images: string[]
  altText?: string
}

export function ImageGallery({ images, altText = 'Property photo' }: ImageGalleryProps) {
  const [active, setActive] = useState(0)

  return (
    <div className="gallery">
      <div className="main">
        {images && images.length > 0 ? (
          <img src={images[active]} alt={`${altText} ${active + 1} of ${images.length}`} loading="lazy" />
        ) : (
          <img src="/placeholder-image.svg" alt="No photos available" className="placeholder" />
        )}
      </div>
      {images && images.length > 1 && (
        <div className="thumbs" role="group" aria-label="Photo thumbnails">
          {images.map((img, i) => (
            <button
              key={i}
              className={i === active ? 'active' : ''}
              onClick={() => setActive(i)}
              aria-label={`Photo ${i + 1} of ${images.length}`}
              aria-current={i === active ? 'true' : undefined}
            >
              <img src={img} alt="" loading="lazy" aria-hidden="true" />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
