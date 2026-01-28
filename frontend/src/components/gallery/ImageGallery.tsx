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
          <img src={images[active]} alt={altText} loading="lazy" />
        ) : (
          <img src="/placeholder-image.svg" alt="No photos" className="placeholder" />
        )}
      </div>
      {images && images.length > 1 && (
        <div className="thumbs">
          {images.map((img, i) => (
            <button
              key={i}
              className={i === active ? 'active' : ''}
              onClick={() => setActive(i)}
              aria-label={`Photo ${i + 1}`}
            >
              <img src={img} alt={altText} loading="lazy" />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
