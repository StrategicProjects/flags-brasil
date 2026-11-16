// Enxuga sem mexer no desenho: mantém os ids (gradientes e <use> de brasões dependem deles).
export default {
  multipass: true,
  floatPrecision: 3,
  plugins: [
    {
      name: 'preset-default',
      params: { overrides: { cleanupIds: false } },
    },
    'removeDimensions',
  ],
};
