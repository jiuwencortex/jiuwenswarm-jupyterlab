const path = require('path');

module.exports = {
  entry: './src/index.ts',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'index.js',
    libraryTarget: 'amd',
    publicPath: '',
  },
  resolve: {
    extensions: ['.ts', '.tsx', '.js', '.jsx'],
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: 'ts-loader',
        exclude: /node_modules/,
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader'],
      },
    ],
  },
  externals: [
    '@jupyterlab/application',
    '@jupyterlab/apputils',
    '@jupyterlab/notebook',
    '@jupyterlab/coreutils',
    '@jupyterlab/ui-components',
    '@jupyterlab/statusbar',
    '@lumino/widgets',
    '@lumino/messaging',
    'react',
    'react-dom',
  ],
};
