"use client";

import { useTranslation } from 'react-i18next';
import { Menu, MenuButton, MenuItem, MenuItems } from "@headlessui/react";

const languages = [
  { code: 'es', label: 'Español' },
  { code: 'en', label: 'English' },
];

export const SelectorIdioma = () => {
  const { i18n } = useTranslation();

  const handleChange = (event) => {
    i18n.changeLanguage(event.target.value);
  };

 return (                                                                                                                                       
    <div className="relative">
      <Menu as="div" className="relative">
        <MenuButton className="flex items-center justify-center gap-2 rounded-xl border border-gray-200 bg-white/70 px-5 py-2 text-sm font-medium text-gray-700 shadow-sm cursor-pointer hover:border-blue-300 focus:outline-none transition-all duration-150">
          <img
            src={i18n.language === 'es' ? '/imagenes_idiomas/espana.png' : '/imagenes_idiomas/reino-unido.png'}
            alt={i18n.language}
            width={20}
            height={20}
            className="rounded-sm"
          />
          {i18n.language === 'es' ? 'Español' : 'English'}
        </MenuButton>

        <MenuItems className="absolute right-0 z-10 mt-2 w-36 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black/5
  focus:outline-none">
          {languages.map((lng) => (
            <MenuItem key={lng.code}>
              {({ active }) => (
                <button
                  onClick={() => i18n.changeLanguage(lng.code)}
                  className={`flex items-center gap-2 w-full px-4 py-2 text-sm ${active ? 'bg-gray-100' : ''}`}
                >
                  <img
                    src={lng.code === 'es' ? '/imagenes_idiomas/espana.png' : '/imagenes_idiomas/reino-unido.png'}
                    alt={lng.label}
                    width={20}
                    height={20}
                    className="rounded-sm"
                  />
                  {lng.label}
                </button>
              )}
            </MenuItem>
          ))}
        </MenuItems>
      </Menu>
    </div>
  );
}